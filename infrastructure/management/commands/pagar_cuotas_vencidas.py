from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from infrastructure.models import Prestamo, Cuenta, CuotaPrestamo, Transaccion


class Command(BaseCommand):
    help = 'Paga automáticamente las cuotas vencidas de préstamos con débito automático'

    def handle(self, *args, **options):
        hoy = date.today()
        cuotas_vencidas = CuotaPrestamo.objects.filter(
            estado='pendiente',
            fecha_vencimiento__lte=hoy,
            prestamo__debito_automatico=True,
            prestamo__estado='activo',
        ).select_related('prestamo__cliente__usuario')

        contador = 0
        errores = 0

        for cuota in cuotas_vencidas:
            with transaction.atomic():
                prestamo = cuota.prestamo
                cliente = prestamo.cliente
                cuentas = cliente.cuentas.filter(estado='activa').order_by('id')

                if not cuentas.exists():
                    errores += 1
                    self.stdout.write(self.style.WARNING(
                        f'Cuota {cuota.id}: {cliente.usuario.username} no tiene cuentas activas'
                    ))
                    continue

                cuenta = cuentas.first()

                cuenta_db = Cuenta.objects.select_for_update().get(id=cuenta.id)
                if cuenta_db.saldo < cuota.monto_cuota:
                    errores += 1
                    self.stdout.write(self.style.WARNING(
                        f'Cuota {cuota.id}: {cliente.usuario.username} - saldo insuficiente (${cuenta_db.saldo} < ${cuota.monto_cuota})'
                    ))
                    continue

                Cuenta.objects.filter(id=cuenta.id).update(saldo=F('saldo') - cuota.monto_cuota)

                cuota.estado = 'pagada'
                cuota.fecha_pago = hoy
                cuota.monto_pagado = cuota.monto_cuota
                cuota.save()

                Transaccion.objects.create(
                    tipo='pago_prestamo',
                    monto=cuota.monto_cuota,
                    cuenta_origen=cuenta,
                    estado='completada',
                    descripcion=f'Pago automático cuota {cuota.numero_cuota} - Préstamo #{prestamo.id}',
                )

                Prestamo.objects.filter(id=prestamo.id).update(saldo_pendiente=F('saldo_pendiente') - cuota.monto_cuota)

                contador += 1

        if contador:
            self.stdout.write(self.style.SUCCESS(f'{contador} cuota(s) pagada(s) automáticamente.'))
        else:
            self.stdout.write('No hay cuotas vencidas para pagar.')

        if errores:
            self.stdout.write(self.style.WARNING(f'{errores} cuota(s) con errores (saldo insuficiente o sin cuenta).'))
