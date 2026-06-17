from datetime import date
from decimal import Decimal
from typing import List, Optional

from django.db import transaction
from django.db.models import Q, F

from domain.entities import CuentaEntity, TransaccionEntity, PrestamoEntity, CuotaEntity
from domain.ports import RepositorioCuenta, RepositorioTransaccion, RepositorioPrestamo
from infrastructure.models import Cuenta, Transaccion, Prestamo, CuotaPrestamo


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
