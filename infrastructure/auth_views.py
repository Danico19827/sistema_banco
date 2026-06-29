from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, CreateView, DetailView, ListView

from .forms import RegistroClienteForm
from .models import Cuenta, Transaccion, Prestamo, CuotaPrestamo, ConfiguracionSeguridad

from application.use_cases import RealizarTransferencia, SolicitarPrestamo, PagarCuota
from infrastructure.adapters.repositories import (
    DjangoCuentaRepository,
    DjangoTransaccionRepository,
    DjangoPrestamoRepository,
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
        messages.success(self.request, f'¡Bienvenido de nuevo, {form.get_user().first_name}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        username = self.request.POST.get('username', '')
        if username:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(username=username)
                conf = ConfiguracionSeguridad.objects.get(cliente__usuario=user)
                conf.intentos_fallidos_login += 1
                if conf.intentos_fallidos_login >= 5:
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


class TransferenciaView(LoginRequiredMixin, TemplateView):
    template_name = 'transferencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuentas'] = self.request.user.cliente.cuentas.filter(estado='activa')
        return context

    def post(self, request, *args, **kwargs):
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

        repo_cuenta = DjangoCuentaRepository()
        repo_tx = DjangoTransaccionRepository()

        try:
            with transaction.atomic():
                caso = RealizarTransferencia(repo_cuenta, repo_tx)
                resultado = caso.ejecutar(
                    cuenta_origen_id=int(cuenta_origen_id),
                    destino_busqueda=destino_raw,
                    monto=monto,
                    descripcion=concepto,
                )

            if resultado.exitoso:
                messages.success(request, 'Transferencia realizada con éxito.')
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
        accion = request.POST.get('accion', '')

        monto = Decimal(request.POST.get('monto', '0'))
        plazo = int(request.POST.get('plazo', '12'))
        sistema = request.POST.get('sistema', 'frances')

        repo_prestamo = DjangoPrestamoRepository()
        repo_cuenta = DjangoCuentaRepository()

        if accion == 'simular':
            use_case = SolicitarPrestamo(repo_prestamo, repo_cuenta)
            cuotas = use_case.simular(monto, plazo, sistema)
            if cuotas is None:
                messages.error(request, 'Monto o plazo fuera de los límites permitidos (min $1,000, máx $1,000,000 | 3-60 meses).')
                return redirect('prestamos_solicitar')

            return render(request, self.template_name, {
                'cuentas': request.user.cliente.cuentas.filter(estado='activa'),
                'simulacion': cuotas,
                'monto': monto,
                'plazo': plazo,
                'sistema': sistema,
                'tasa': SolicitarPrestamo.TASA_ANUAL,
            })

        elif accion == 'confirmar':
            try:
                with transaction.atomic():
                    use_case = SolicitarPrestamo(repo_prestamo, repo_cuenta)
                    prestamo, mensaje = use_case.ejecutar(
                        cliente_id=request.user.cliente.id,
                        monto=monto,
                        plazo_meses=plazo,
                        sistema=sistema,
                    )

                    if prestamo:
                        repo_cuenta.incrementar_saldo(
                            request.user.cliente.cuentas.first().id, monto
                        )
                        messages.success(request, mensaje)
                        return redirect('prestamos')
                    else:
                        messages.error(request, mensaje)
                        return redirect('prestamos_solicitar')

            except Exception:
                messages.error(request, 'Error al procesar el préstamo. Verificá los datos.')
                return redirect('prestamos_solicitar')

        messages.error(request, 'Acción no reconocida.')
        return redirect('prestamos_solicitar')


class PrestamoDetalleView(LoginRequiredMixin, DetailView):
    template_name = 'prestamos/detalle.html'
    context_object_name = 'prestamo'

    def get_queryset(self):
        return Prestamo.objects.filter(cliente=self.request.user.cliente)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuotas'] = self.object.cuotas.order_by('numero_cuota')
        context['cuentas'] = self.request.user.cliente.cuentas.filter(estado='activa')
        return context

    def post(self, request, *args, **kwargs):
        cuota_id = request.POST.get('cuota_id')
        cuenta_id = request.POST.get('cuenta_id')

        if not cuota_id or not cuenta_id:
            messages.error(request, 'Faltan datos para procesar el pago.')
            return redirect('prestamo_detalle', pk=self.kwargs['pk'])

        repo_prestamo = DjangoPrestamoRepository()
        repo_cuenta = DjangoCuentaRepository()

        try:
            with transaction.atomic():
                use_case = PagarCuota(repo_prestamo, repo_cuenta)
                ok, mensaje = use_case.ejecutar(
                    int(cuota_id), int(cuenta_id), request.user.cliente.id
                )

            if ok:
                messages.success(request, mensaje)
            else:
                messages.error(request, mensaje)

        except Exception:
            messages.error(request, 'Error al procesar el pago.')

        return redirect('prestamo_detalle', pk=self.kwargs['pk'])
    

class MetricasView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'metricas.html'

    def test_func(self):
        return self.request.user.is_active and self.request.user.is_superuser