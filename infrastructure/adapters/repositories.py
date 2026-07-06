from datetime import date
from decimal import Decimal
from typing import List, Optional

from django.db import transaction
from django.db.models import Q, F, Count, Sum

from domain.entities import CuentaEntity, TransaccionEntity, PrestamoEntity, CuotaEntity
from domain.ports import RepositorioCuenta, RepositorioTransaccion, RepositorioPrestamo, RepositorioCliente
from infrastructure.models import ConfiguracionSeguridad, Cuenta, Transaccion, Prestamo, CuotaPrestamo, Cliente

from typing import List, Optional, Dict, Any
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone

def _cuenta_a_entity(c: Cuenta) -> CuentaEntity:
    return CuentaEntity(
        id=c.id,
        cliente_id=c.cliente_id,
        tipo_cuenta=c.tipo_cuenta,
        numero_cuenta=c.numero_cuenta or '',
        alias=c.alias,
        cvu=c.cvu,
        saldo=c.saldo,
        moneda=c.moneda,
        estado=c.estado,
        limite_transferencia_diario=c.limite_transferencia_diario,
    )


def _tx_a_entity(t: Transaccion) -> TransaccionEntity:
    return TransaccionEntity(
        id=t.id,
        tipo=t.tipo,
        monto=t.monto,
        cuenta_origen_id=t.cuenta_origen_id,
        cuenta_destino_id=t.cuenta_destino_id,
        descripcion=t.descripcion,
        estado=t.estado,
        fecha_creacion=t.fecha_creacion,
        riesgo_fraude=t.riesgo_fraude,
        es_fraude_confirmado=t.es_fraude_confirmado,
    )


def _prestamo_a_entity(p: Prestamo) -> PrestamoEntity:
    cuotas = [_cuota_a_entity(c) for c in p.cuotas.all().order_by('numero_cuota')]
    return PrestamoEntity(
        id=p.id,
        cliente_id=p.cliente_id,
        monto_original=p.monto_original,
        saldo_pendiente=p.saldo_pendiente,
        tasa_interes_anual=p.tasa_interes_anual,
        plazo_meses=p.plazo_meses,
        sistema_amortizacion=p.sistema_amortizacion,
        estado=p.estado,
        cuotas=cuotas,
    )


def _cuota_a_entity(c: CuotaPrestamo) -> CuotaEntity:
    return CuotaEntity(
        id=c.id,
        prestamo_id=c.prestamo_id,
        numero_cuota=c.numero_cuota,
        monto_cuota=c.monto_cuota,
        fecha_vencimiento=c.fecha_vencimiento,
        estado=c.estado,
        fecha_pago=c.fecha_pago,
        monto_pagado=c.monto_pagado,
    )


class DjangoCuentaRepository(RepositorioCuenta):

    def buscar_por_id_con_bloqueo(self, cuenta_id: int) -> Optional[CuentaEntity]:
        try:
            c = Cuenta.objects.select_for_update().get(id=cuenta_id)
            return _cuenta_a_entity(c)
        except Cuenta.DoesNotExist:
            return None

    def buscar_por_alias_o_cvu(self, valor: str) -> Optional[CuentaEntity]:
        try:
            c = Cuenta.objects.get(
                Q(alias=valor) | Q(cvu=valor) | Q(numero_cuenta=valor) | Q(id=valor)
            )
            return _cuenta_a_entity(c)
        except (Cuenta.DoesNotExist, ValueError):
            return None

    def listar_por_cliente(self, cliente_id: int) -> List[CuentaEntity]:
        return [_cuenta_a_entity(c) for c in Cuenta.objects.filter(cliente_id=cliente_id)]

    def listar_por_cliente_activas(self, cliente_id: int) -> List[CuentaEntity]:
        return [_cuenta_a_entity(c) for c in Cuenta.objects.filter(cliente_id=cliente_id, estado='activa')]

    def incrementar_saldo(self, cuenta_id: int, delta: Decimal) -> None:
        Cuenta.objects.filter(id=cuenta_id).update(saldo=F('saldo') + delta)


class DjangoTransaccionRepository(RepositorioTransaccion):

    def crear(self, transaccion: TransaccionEntity) -> TransaccionEntity:
        t = Transaccion.objects.create(
            tipo=transaccion.tipo,
            monto=transaccion.monto,
            cuenta_origen_id=transaccion.cuenta_origen_id,
            cuenta_destino_id=transaccion.cuenta_destino_id,
            descripcion=transaccion.descripcion,
            estado=transaccion.estado,
        )
        return _tx_a_entity(t)

    def listar_por_cuenta(self, cuenta_id: int, limite: int = 10) -> List[TransaccionEntity]:
        txs = Transaccion.objects.filter(
            Q(cuenta_origen_id=cuenta_id) | Q(cuenta_destino_id=cuenta_id)
        ).order_by('-fecha_creacion')[:limite]
        return [_tx_a_entity(t) for t in txs]

    def listar_por_cliente(self, cliente_id: int, limite: int = 10) -> List[TransaccionEntity]:
        cuentas_ids = Cuenta.objects.filter(cliente_id=cliente_id).values_list('id', flat=True)
        txs = Transaccion.objects.filter(
            Q(cuenta_origen_id__in=cuentas_ids) | Q(cuenta_destino_id__in=cuentas_ids)
        ).order_by('-fecha_creacion')[:limite]
        return [_tx_a_entity(t) for t in txs]


class DjangoPrestamoRepository(RepositorioPrestamo):

    def crear(self, prestamo: PrestamoEntity, cuotas: List[CuotaEntity]) -> PrestamoEntity:
        with transaction.atomic():
            p = Prestamo.objects.create(
                cliente_id=prestamo.cliente_id,
                monto_original=prestamo.monto_original,
                saldo_pendiente=prestamo.saldo_pendiente,
                tasa_interes_anual=prestamo.tasa_interes_anual,
                plazo_meses=prestamo.plazo_meses,
                sistema_amortizacion=prestamo.sistema_amortizacion,
                estado=prestamo.estado,
            )
            for cuota in cuotas:
                CuotaPrestamo.objects.create(
                    prestamo_id=p.id,
                    numero_cuota=cuota.numero_cuota,
                    monto_cuota=cuota.monto_cuota,
                    fecha_vencimiento=cuota.fecha_vencimiento,
                    estado=cuota.estado,
                )
        return _prestamo_a_entity(p)

    def listar_por_cliente(self, cliente_id: int) -> List[PrestamoEntity]:
        prestamos = Prestamo.objects.filter(cliente_id=cliente_id).prefetch_related('cuotas').order_by('-fecha_inicio')
        return [_prestamo_a_entity(p) for p in prestamos]

    def buscar_por_id(self, prestamo_id: int) -> Optional[PrestamoEntity]:
        try:
            p = Prestamo.objects.prefetch_related('cuotas').get(id=prestamo_id)
            return _prestamo_a_entity(p)
        except Prestamo.DoesNotExist:
            return None

    def pagar_cuota(self, cuota_id: int, monto: Decimal, fecha_pago: date) -> None:
        with transaction.atomic():
            cuota = CuotaPrestamo.objects.select_for_update().get(id=cuota_id)
            cuota.estado = 'pagada'
            cuota.fecha_pago = fecha_pago
            cuota.monto_pagado = monto
            cuota.save()

            prestamo = Prestamo.objects.select_for_update().get(id=cuota.prestamo_id)
            prestamo.saldo_pendiente = F('saldo_pendiente') - monto
            prestamo.save(update_fields=['saldo_pendiente'])
            prestamo.refresh_from_db()
            if prestamo.saldo_pendiente <= 0:
                prestamo.saldo_pendiente = Decimal('0.00')
                prestamo.estado = 'pagado'
                prestamo.save(update_fields=['saldo_pendiente', 'estado'])

# Métodos implementados para la realización de las métricas
class DjangoClienteRepository(RepositorioCliente):
    def listar_clientes_con_cuentas_activas(self) -> List[int]:
        # es para separar usuarios que tengan al menos un cuenta activa
        clientes_ids = Cliente.objects.filter(
            estado__iexact='activo'
        ).values_list('id', flat=True).distinct()
        
        return list(clientes_ids)
        
    def obtener_score_por_cliente(self, cliente_id: int) -> int:
        cliente = Cliente.objects.get(id=cliente_id)
        return cliente.score_crediticio_inicial

    def obtener_monitoreo_seguridad(self) -> List[Dict[str, Any]]:
        # obtiene el top 3 de usuarios con mas intentos fallidos
        configuraciones = (
            ConfiguracionSeguridad.objects
            .select_related('cliente__usuario')
            .order_by('-intentos_fallidos_login')[:3]
        )
        
        ahora = timezone.now()
        resultado = []
        
        for config in configuraciones:
            esta_bloqueado = config.bloqueado_hasta and config.bloqueado_hasta > ahora
            estado_str = 'Bloqueado' if (esta_bloqueado or config.intentos_fallidos_login >= 3) else 'Normal'
            
            resultado.append({
                'usuario': config.cliente.usuario.username,
                'intentos': config.intentos_fallidos_login,
                'estado': estado_str
            })
            
        return resultado
    
    def obtener_distribucion_pagadores_por_genero(self) -> Dict[str, int]:
        ahora = timezone.now().date()
        
        clientes_con_mora = Cliente.objects.filter(
            prestamos__cuotas__estado='pendiente',
            prestamos__cuotas__fecha_vencimiento__lt=ahora
        ).values_list('id', flat=True).distinct()
        
        resultado_query = (
            Cliente.objects
            .exclude(id__in=clientes_con_mora)
            .values('genero')
            .annotate(total=Count('id'))
        )
        
        distribucion = {
            'Femenino': 0,
            'Masculino': 0,
            'No especifica': 0
        }
        
        map_generos = {
            'F': 'Femenino',
            'M': 'Masculino',
            'N': 'No especifica'
        }
        
        for fila in resultado_query:
            genero_db = fila['genero']
            genero_legible = map_generos.get(genero_db, 'No especifica')
            distribucion[genero_legible] = fila['total']
            
        return distribucion

    ## Este metodo nuevo se utiliza para analizar el camino inverso, es decir morosos por género
    ## solo usar para la demostracion
    def obtener_distribucion_morosos_por_genero(self) -> Dict[str, int]:
        ahora = timezone.now().date()
        
        # 1. La misma lista de clientes con cuotas vencidas/pendientes
        clientes_con_mora = Cliente.objects.filter(
            prestamos__cuotas__estado='pendiente',
            prestamos__cuotas__fecha_vencimiento__lt=ahora
        ).values_list('id', flat=True).distinct()
        
        # 2. El opuesto: En vez de exclude, usamos filter para quedarnos con los clientes morosos
        resultado_query = (
            Cliente.objects
            .filter(id__in=clientes_con_mora) 
            .values('genero')
            .annotate(total=Count('id'))
        )
        
        # 3. El mapeo idéntico para que el frontend lo entienda
        distribucion = {'Femenino': 0, 'Masculino': 0, 'No especifica': 0}
        map_generos = {'F': 'Femenino', 'M': 'Masculino', 'N': 'No especifica'}
        
        for fila in resultado_query:
            genero_db = fila['genero']
            genero_legible = map_generos.get(genero_db, 'No especifica')
            distribucion[genero_legible] = fila['total']
            
        return distribucion

    def obtener_evolucion_cantidad_prestamos_por_educacion(self) -> Dict[str, List[int]]:
        """
        Cuenta préstamos acumulados por mes y NIVEL EDUCATIVO del cliente.
        Categorías: Primario, Secundario, Terciario/Universitario.
        """
        ahora = timezone.now()
        
        # 1. Agrupamos por mes y por el nivel educativo del cliente
        resultado_query = (
            Prestamo.objects
            .filter(fecha_inicio__year=ahora.year)
            .annotate(mes=ExtractMonth('fecha_inicio')) 
            .values('mes', 'cliente__nivel_educativo')
            .annotate(cantidad=Count('id'))               
            .order_by('mes')
        )
        
        # 2. Inicializamos las listas para los primeros 6 meses (Ene a Jun)
        estructura_vacia = {
            'Primario': [0] * 6,
            'Secundario': [0] * 6,
            'Terciario/Universitario': [0] * 6
        }
        
        # 3. Mapeo de cómo está en la BD a las claves del diccionario
        # Ajustá las claves (izq) a los valores exactos de la base de datos
        map_educacion = {
            'primario': 'Primario',
            'secundario': 'Secundario',
            'terciario': 'Terciario/Universitario',
            'universitario': 'Terciario/Universitario',
            'posgrado': 'Terciario/Universitario'  # Sumamos los posgrados a la categoría superior
        }
        
        # 4. Llenamos los campos correspondientes
        for fila in resultado_query:
            educacion_db = fila['cliente__nivel_educativo']
            # Si viene algo raro o nulo, lo ignoramos o lo sumamos a alguna categoría por defecto
            educacion_vista = map_educacion.get(educacion_db)
            
            if educacion_vista: # Solo si mapeó correctamente
                mes = fila['mes']
                idx_mes = mes - 1
                
                if idx_mes < 6:
                    estructura_vacia[educacion_vista][idx_mes] += fila['cantidad']
        
        # 5. Volvemos la lista acumulativa mes a mes
        for nivel in estructura_vacia:
            acumulado = 0
            for i in range(6):
                acumulado += estructura_vacia[nivel][i]
                estructura_vacia[nivel][i] = acumulado
                    
        return estructura_vacia
    
    def obtener_datos_riesgo_por_edad(self) -> List[Dict[str, Any]]:
        """
        Query compleja estilo minería de datos para el gráfico de burbujas
        Calcula Edad, Cantidad, Monto Total y Riesgo de mora
        """
        ahora = date.today()
        
        # 1. Obtenemos datos crudos de clientes y sus préstamos
        query = Cliente.objects.annotate(
            # Calculamos la edad al vuelo (AñoActual - AñoNacimiento)
            edad=ahora.year - ExtractYear('fecha_nacimiento')
        ).prefetch_related('prestamos')
        
        resultado = []
        
        # 2. Iteramos para calcular las métricas por cliente de forma manual para evitar duplicados en annotations complejas
        # (Es más prolijo y fácil de debuggear que una query gigante con subqueries)
        for cliente in query:
            prestamos = cliente.prestamos.all()
            total_prestamos = prestamos.count()
            
            if total_prestamos == 0:
                continue # Saltamos clientes sin préstamos

            monto_total_solicitado = prestamos.aggregate(total=Sum('monto_original'))['total'] or 0
            
            # Determinamos RIESGO: Si tiene al menos UN préstamo 'vencido', todo el cliente es Rojo.
            tiene_mora = prestamos.filter(estado='vencido').exists()
            riesgo = 'En Mora' if tiene_mora else 'Pagó a Tiempo'
            
            # Formateamos el objeto para el JS
            resultado.append({
                'x': cliente.edad,                    # Eje X
                'y': total_prestamos,                  # Eje Y
                'r': float(monto_total_solicitado),    # Tamaño Burbuja (dinero crudo, lo normalizamos en JS)
                'riesgo': riesgo                       # Categoría de color
            })
            
        return resultado

    