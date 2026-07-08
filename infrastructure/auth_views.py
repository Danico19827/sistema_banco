from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, CreateView, DetailView, ListView

from .forms import RegistroClienteForm
from .models import Cuenta, Transaccion, Prestamo, CuotaPrestamo, ConfiguracionSeguridad


from application.use_cases import (
    RealizarTransferencia, SolicitarPrestamo, PagarCuota,
    ObtenerTopIntentosFallidos, CalcularPromedioScoreClientesActivos,
    ObtenerDistribucionPagadoresPorGenero, ObtenerEvolucionCantidadPrestamosPorEducacion,
    ObtenerDatosRiesgoEdadUseCase, ConstituirPlazoFijo, CancelarPlazoFijo,
)
from infrastructure.adapters.repositories import (
    DjangoCuentaRepository,
    DjangoTransaccionRepository,
    DjangoPrestamoRepository, DjangoClienteRepository, DjangoPlazoFijoRepository,
)

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
class InicioView(TemplateView):
    template_name = 'inicio.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('panel')
        return super().dispatch(request, *args, **kwargs)


class RegistroView(CreateView):
    form_class = RegistroClienteForm
    template_name = 'registro.html'
    success_url = reverse_lazy('panel')

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
        login(self.request, self.object)
        messages.success(self.request, f'¡Bienvenido {self.object.first_name}! Tu cuenta fue creada con éxito.')
        return redirect(self.get_success_url())


class InicioSesionView(BaseLoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        user = form.get_user()
        try:
            conf = ConfiguracionSeguridad.objects.get(cliente__usuario=user)
            if conf.bloqueado_hasta and conf.bloqueado_hasta > timezone.now():
                messages.error(self.request, 'Cuenta bloqueada por 15 minutos por demasiados intentos fallidos.')
                return redirect('inicio_sesion')
            conf.intentos_fallidos_login = 0
            conf.bloqueado_hasta = None
            conf.save()
        except ConfiguracionSeguridad.DoesNotExist:
            pass
        messages.success(self.request, f'¡Bienvenido de nuevo, {user.first_name}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        username = self.request.POST.get('username', '')
        if username:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(username=username)
                conf = ConfiguracionSeguridad.objects.get(cliente__usuario=user)
                if conf.bloqueado_hasta and conf.bloqueado_hasta > timezone.now():
                    messages.error(self.request, 'Cuenta bloqueada por 15 minutos por demasiados intentos fallidos.')
                    return redirect('inicio_sesion')
                conf.intentos_fallidos_login += 1
                if conf.intentos_fallidos_login >= 3:
                    conf.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
                    conf.save()
                    messages.error(self.request, 'Demasiados intentos fallidos. Cuenta bloqueada por 15 minutos.')
                    return redirect('inicio_sesion')
                conf.save()
            except (User.DoesNotExist, ConfiguracionSeguridad.DoesNotExist):
                pass
        return super().form_invalid(form)


class PanelView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cliente = self.request.user.cliente
        cuentas = cliente.cuentas.all()
        cuentas_ids = list(cuentas.values_list('id', flat=True))
        transacciones = Transaccion.objects.filter(
            Q(cuenta_origen__in=cuentas) | Q(cuenta_destino__in=cuentas)
        ).order_by('-fecha_creacion')[:10]
        prestamos = Prestamo.objects.filter(cliente=cliente).order_by('-fecha_inicio')[:5]

        context['cliente'] = cliente
        context['cuentas'] = cuentas
        context['cuentas_ids'] = cuentas_ids
        context['transacciones'] = transacciones
        context['prestamos'] = prestamos
        return context


class HistorialView(LoginRequiredMixin, ListView):
    template_name = 'historial.html'
    context_object_name = 'transacciones'
    paginate_by = 25

    def get_queryset(self):
        cuentas = self.request.user.cliente.cuentas.all()
        qs = Transaccion.objects.filter(
            Q(cuenta_origen__in=cuentas) | Q(cuenta_destino__in=cuentas)
        )
        tipo = self.request.GET.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        desde = self.request.GET.get('desde')
        if desde:
            qs = qs.filter(fecha_creacion__date__gte=desde)
        hasta = self.request.GET.get('hasta')
        if hasta:
            qs = qs.filter(fecha_creacion__date__lte=hasta)
        return qs.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuentas_ids'] = list(self.request.user.cliente.cuentas.values_list('id', flat=True))
        context['tipos'] = Transaccion.TIPO_TRANSACCION
        context['filtro_tipo'] = self.request.GET.get('tipo', '')
        context['filtro_desde'] = self.request.GET.get('desde', '')
        context['filtro_hasta'] = self.request.GET.get('hasta', '')
        return context


class TransferenciaView(LoginRequiredMixin, TemplateView):
    template_name = 'transferencia.html'
    UMBRAL_2FA = Decimal('10000.00')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuentas'] = self.request.user.cliente.cuentas.filter(estado='activa')
        context['otp_pendiente'] = self.request.session.get('otp_codigo') is not None
        return context

    def post(self, request, *args, **kwargs):
        config = request.user.cliente.configuracion_seguridad

        # Verificar OTP si está pendiente
        codigo_ingresado = request.POST.get('codigo_otp', '').strip()
        if codigo_ingresado:
            otp_codigo = request.session.pop('otp_codigo', None)
            otp_expira = request.session.pop('otp_expira', None)
            otp_datos = request.session.pop('otp_datos', None)

            if otp_codigo is None or otp_expira is None or otp_datos is None:
                messages.error(request, 'No hay un código OTP pendiente. Iniciá la transferencia de nuevo.')
                return redirect('transferencia')

            if timezone.now() > otp_expira:
                messages.error(request, 'El código OTP expiró. Iniciá la transferencia de nuevo.')
                return redirect('transferencia')

            if str(otp_codigo) != codigo_ingresado:
                messages.error(request, 'Código OTP incorrecto.')
                return redirect('transferencia')

            return self._ejecutar_transferencia(request, otp_datos)

        cuenta_origen_id = request.POST.get('cuenta_origen')
        destino_raw = request.POST.get('cuenta_destino', '').strip()
        monto_str = request.POST.get('monto', '0')
        concepto = request.POST.get('concepto', '')

        try:
            monto = Decimal(monto_str)
            if monto <= 0:
                raise ValueError
        except (Exception, ValueError):
            messages.error(request, 'El monto debe ser un número positivo.')
            return redirect('transferencia')

        if not destino_raw:
            messages.error(request, 'Debe indicar una cuenta destino.')
            return redirect('transferencia')

        if config.doble_factor_activo and monto >= self.UMBRAL_2FA:
            import random
            otp = random.randint(100000, 999999)
            request.session['otp_codigo'] = str(otp)
            request.session['otp_expira'] = timezone.now() + timedelta(minutes=5)
            request.session['otp_datos'] = {
                'cuenta_origen_id': cuenta_origen_id,
                'destino_raw': destino_raw,
                'monto': str(monto),
                'descripcion': concepto,
            }
            messages.info(request, f'Código OTP generado. Ingresalo para confirmar la transferencia.')
            return redirect('transferencia')

        return self._ejecutar_transferencia(request, {
            'cuenta_origen_id': cuenta_origen_id,
            'destino_raw': destino_raw,
            'monto': str(monto),
            'descripcion': concepto,
        })

    def _ejecutar_transferencia(self, request, datos):
        cuenta_origen_id = datos['cuenta_origen_id']
        destino_raw = datos['destino_raw']
        monto = Decimal(datos['monto'])
        concepto = datos.get('descripcion', '')

        repo_cuenta = DjangoCuentaRepository()
        repo_tx = DjangoTransaccionRepository()

        try:
            from infrastructure.adapters.fraude_adapter import evaluar_transferencia
            motor = type('MotorFraudAdapter', (), {'evaluar': staticmethod(evaluar_transferencia)})

            with transaction.atomic():
                caso = RealizarTransferencia(repo_cuenta, repo_tx, motor_fraude=motor)
                resultado = caso.ejecutar(
                    cuenta_origen_id=int(cuenta_origen_id),
                    destino_busqueda=destino_raw,
                    monto=monto,
                    descripcion=concepto,
                )

            if resultado.exitoso:
                if resultado.riesgo_fraude >= 0.7:
                    from infrastructure.models import AlertaFraude
                    AlertaFraude.objects.create(
                        transaccion_id=resultado.tx_id,
                        score_riesgo=resultado.riesgo_fraude,
                        accion_tomada='notificacion_cliente',
                    )
                messages.success(request, resultado.mensaje)
                return redirect('panel')
            else:
                messages.error(request, resultado.mensaje)
                return redirect('transferencia')

        except (Cuenta.DoesNotExist, ValueError):
            messages.error(request, 'Cuenta origen inválida o inactiva.')
            return redirect('transferencia')


class PrestamoListView(LoginRequiredMixin, ListView):
    template_name = 'prestamos/lista.html'
    context_object_name = 'prestamos'

    def get_queryset(self):
        return Prestamo.objects.filter(
            cliente=self.request.user.cliente
        ).order_by('-fecha_inicio')


class PrestamoCrearView(LoginRequiredMixin, TemplateView):
    template_name = 'prestamos/solicitar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuentas'] = self.request.user.cliente.cuentas.filter(estado='activa')
        return context

    def post(self, request, *args, **kwargs):
        monto_str = request.POST.get('monto', '0').strip()
        plazo = request.POST.get('plazo', '12')
        sistema = request.POST.get('sistema', 'frances')
        cuenta_id = request.POST.get('cuenta_id')
        debito_automatico = request.POST.get('debito_automatico') == 'on'

        try:
            monto = Decimal(monto_str)
        except (ValueError, ArithmeticError):
            messages.error(request, 'Monto inválido.')
            return redirect('prestamos_solicitar')

        if monto < 1000 or monto > 1000000:
            messages.error(request, 'El monto debe estar entre $1.000 y $1.000.000.')
            return redirect('prestamos_solicitar')

        try:
            plazo = int(plazo)
            if plazo < 3 or plazo > 60:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'El plazo debe ser entre 3 y 60 meses.')
            return redirect('prestamos_solicitar')

        if sistema not in ('frances', 'aleman'):
            messages.error(request, 'Sistema de amortización inválido.')
            return redirect('prestamos_solicitar')

        if not cuenta_id:
            messages.error(request, 'Seleccioná la cuenta donde recibir el dinero.')
            return redirect('prestamos_solicitar')

        repo_prestamo = DjangoPrestamoRepository()
        repo_cuenta = DjangoCuentaRepository()

        try:
            with transaction.atomic():
                from infrastructure.adapters.scoring_adapter import evaluar_cliente
                motor = type('MotorScoringAdapter', (), {'evaluar': staticmethod(evaluar_cliente)})
                use_case = SolicitarPrestamo(repo_prestamo, repo_cuenta, motor_scoring=motor)
                prestamo, mensaje = use_case.ejecutar(
                    cliente_id=request.user.cliente.id,
                    monto=monto,
                    plazo_meses=plazo,
                    sistema=sistema,
                )

                if prestamo:
                    repo_cuenta.incrementar_saldo(int(cuenta_id), monto)
                    if debito_automatico:
                        from infrastructure.models import Prestamo
                        Prestamo.objects.filter(id=prestamo.id).update(debito_automatico=True)
                    messages.success(request, mensaje)
                    return redirect('prestamos')
                else:
                    messages.error(request, mensaje)
                    return redirect('prestamos_solicitar')

        except Exception:
            messages.error(request, 'Error al procesar el préstamo. Verificá los datos.')
            return redirect('prestamos_solicitar')


class PrestamoDetalleView(LoginRequiredMixin, DetailView):
    template_name = 'prestamos/detalle.html'
    context_object_name = 'prestamo'

    def get_queryset(self):
        return Prestamo.objects.filter(cliente=self.request.user.cliente)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.cuotas.filter(estado='pendiente', fecha_vencimiento__lt=date.today()).update(estado='vencida')
        context['cuotas'] = self.object.cuotas.order_by('numero_cuota')
        context['cuentas'] = self.request.user.cliente.cuentas.filter(estado='activa')
        return context

    def post(self, request, *args, **kwargs):
        cuota_id = request.POST.get('cuota_id')
        cuenta_id = request.POST.get('cuenta_id')

        if not cuota_id or not cuenta_id:
            messages.error(request, 'Faltan datos para procesar el pago.')
            return redirect('prestamo_detalle', pk=self.kwargs['pk'])

        from infrastructure.models import CuotaPrestamo, Transaccion
        try:
            cuota = CuotaPrestamo.objects.get(id=int(cuota_id))
        except CuotaPrestamo.DoesNotExist:
            messages.error(request, 'Cuota no encontrada.')
            return redirect('prestamo_detalle', pk=self.kwargs['pk'])

        monto_cuota = cuota.monto_cuota
        repo_prestamo = DjangoPrestamoRepository()
        repo_cuenta = DjangoCuentaRepository()

        try:
            with transaction.atomic():
                use_case = PagarCuota(repo_prestamo, repo_cuenta)
                ok, mensaje = use_case.ejecutar(
                    int(cuota_id), int(cuenta_id), request.user.cliente.id
                )

            if ok:
                Transaccion.objects.create(
                    tipo='pago_prestamo',
                    monto=monto_cuota,
                    cuenta_origen_id=int(cuenta_id),
                    estado='completada',
                    descripcion=f'Pago cuota #{cuota.numero_cuota} - Préstamo #{cuota.prestamo_id}',
                )
                messages.success(request, mensaje)
            else:
                messages.error(request, mensaje)

        except Exception:
            messages.error(request, 'Error al procesar el pago.')

        return redirect('prestamo_detalle', pk=self.kwargs['pk'])
    

# Métodos para la administración de métricas y estádisticas del sistema
class MetricasView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'metricas.html'

    def test_func(self):
        return self.request.user.is_active and self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        # 1. Recuperamos el contexto base de la clase
        contexto = super().get_context_data(**kwargs)
        
        # 2. Instanciamos la arquitectura limpia (lo que ya conocemos)
        repo_cliente = DjangoClienteRepository()
        repo_prestamo = DjangoPrestamoRepository()
        caso_de_uso = CalcularPromedioScoreClientesActivos(repo_cliente, repo_prestamo)
        
        # 3. Calculamos el promedio
        promedio = caso_de_uso.ejecutar()
        
        # 4. Inyectamos el valor en la "canasta" que va al HTML, en criollo: vuelca los datos en la plantilla html.
        contexto['promedio_score'] = promedio


        # ==========================================
        # MÉTRICA B: SEGURIDAD DIL SISTEMA (Intentos fallidos de Login)
        # ==========================================
        caso_de_uso_seguridad = ObtenerTopIntentosFallidos(repo_cliente)
        alertas_login = caso_de_uso_seguridad.ejecutar()
        contexto['alertas_login'] = alertas_login  # Se va al MISMO HTML

        # =========================================================
        # MÉTRICA C: PAGADORES POR GÉNERO
        # =========================================================
        caso_genero = ObtenerDistribucionPagadoresPorGenero(repo_cliente)
        
        # 1. Guardamos el diccionario en 'distribucion'
        distribucion = caso_genero.ejecutar() 
        
        # 2. Usamos 'distribucion' (y no distribucion_pagadores) para armar la lista
        datos_grafico_genero = [
            distribucion.get('Femenino', 0),
            distribucion.get('Masculino', 0),
            distribucion.get('No especifica', 0)
        ]

        contexto['datos_genero'] = datos_grafico_genero
        
        # =========================================================
        # MÉTRICA D: EVOLUCIÓN TEMPORAL POR EDUCACIÓN
        # =========================================================
        caso_educacion = ObtenerEvolucionCantidadPrestamosPorEducacion(
            repo_cliente=DjangoClienteRepository() 
        )
        evolucion_educacion = caso_educacion.ejecutar() 
        
        # Pasamos las nuevas llaves al contexto
        contexto['cantidades_primario'] = evolucion_educacion.get('Primario', [0]*6)
        contexto['cantidades_secundario'] = evolucion_educacion.get('Secundario', [0]*6)
        contexto['cantidades_superior'] = evolucion_educacion.get('Terciario/Universitario', [0]*6)


        # =========================================================
        # MÉTRICA A: Gráfico de burbujas de riesgo por edad
        # =========================================================
        # Instanciamos el caso de uso del gráfico de burbujas
        use_case_riesgo = ObtenerDatosRiesgoEdadUseCase(
            repo_cliente=DjangoClienteRepository()
        )

        # Obtenemos los datos para las burbujas
        datos_burbujas_crudos = use_case_riesgo.ejecutar()

        datos_finales_burbujas = datos_burbujas_crudos

        # Pasamos los datos crudos al contexto
        contexto['datos_riesgo_burbujas'] = datos_finales_burbujas

        return contexto


class PlazoFijoListView(LoginRequiredMixin, ListView):
    template_name = 'plazofijo/lista.html'
    context_object_name = 'plazos_fijos'

    def get_queryset(self):
        repo = DjangoPlazoFijoRepository()
        return repo.listar_por_cliente(self.request.user.cliente.id)


class PlazoFijoCrearView(LoginRequiredMixin, TemplateView):
    template_name = 'plazofijo/crear.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuentas'] = self.request.user.cliente.cuentas.filter(estado='activa')
        return context

    def post(self, request, *args, **kwargs):
        cuenta_id = request.POST.get('cuenta_id')
        monto_str = request.POST.get('monto', '0')
        plazo_dias_str = request.POST.get('plazo_dias', '30')

        try:
            monto = Decimal(monto_str)
            plazo_dias = int(plazo_dias_str)
        except (Exception, ValueError):
            messages.error(request, 'Datos inválidos.')
            return redirect('plazofijo_crear')

        repo_plazo = DjangoPlazoFijoRepository()
        repo_cuenta = DjangoCuentaRepository()

        use_case = ConstituirPlazoFijo(repo_plazo, repo_cuenta)
        plazo, mensaje = use_case.ejecutar(
            cliente_id=request.user.cliente.id,
            cuenta_id=int(cuenta_id),
            monto=monto,
            plazo_dias=plazo_dias,
        )

        if plazo:
            messages.success(request, mensaje)
            return redirect('plazofijo')
        else:
            messages.error(request, mensaje)
            return redirect('plazofijo_crear')


class PlazoFijoCancelarView(LoginRequiredMixin, TemplateView):

    def post(self, request, *args, **kwargs):
        plazo_id = kwargs.get('pk')

        repo_plazo = DjangoPlazoFijoRepository()
        repo_cuenta = DjangoCuentaRepository()

        use_case = CancelarPlazoFijo(repo_plazo, repo_cuenta)
        ok, mensaje = use_case.ejecutar(
            plazo_id=int(plazo_id),
            cliente_id=request.user.cliente.id,
        )

        if ok:
            messages.success(request, mensaje)
        else:
            messages.error(request, mensaje)

        return redirect('plazofijo')


class DepositarView(LoginRequiredMixin, TemplateView):
    template_name = 'depositar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cuentas'] = Cuenta.objects.filter(
            cliente=self.request.user.cliente,
            estado='activa',
        )
        return ctx

    def post(self, request, *args, **kwargs):
        cuenta_id = request.POST.get('cuenta_id')
        monto_str = request.POST.get('monto')

        if not cuenta_id or not monto_str:
            messages.error(request, 'Completá todos los campos.')
            return redirect('depositar')

        try:
            monto = Decimal(monto_str)
        except (ValueError, ArithmeticError):
            messages.error(request, 'Monto inválido.')
            return redirect('depositar')

        if monto <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
            return redirect('depositar')

        try:
            cuenta = Cuenta.objects.select_for_update().get(
                id=cuenta_id,
                cliente=request.user.cliente,
                estado='activa',
            )
        except Cuenta.DoesNotExist:
            messages.error(request, 'Cuenta no encontrada.')
            return redirect('depositar')

        with transaction.atomic():
            from django.db.models import F
            Cuenta.objects.filter(id=cuenta.id).update(saldo=F('saldo') + monto)
            Transaccion.objects.create(
                tipo='deposito',
                monto=monto,
                cuenta_destino=cuenta,
                estado='completada',
                descripcion='Carga de saldo',
            )

        messages.success(request, f'Se cargaron ${monto:,.2f} en tu cuenta.')
        return redirect('panel')


class PerfilView(LoginRequiredMixin, TemplateView):
    template_name = 'perfil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = self.request.user.cliente.configuracion_seguridad
        return context

    def post(self, request, *args, **kwargs):
        config = request.user.cliente.configuracion_seguridad
        config.doble_factor_activo = request.POST.get('doble_factor') == 'on'
        config.save()
        estado = 'activado' if config.doble_factor_activo else 'desactivado'
        messages.success(request, f'2FA {estado} correctamente.')
        return redirect('perfil')
    
