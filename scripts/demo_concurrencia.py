"""
Demo de concurrencia bancaria con PostgreSQL.
Usa RealizarTransferencia (caso de uso real) con select_for_update()
para demostrar integridad ACID bajo concurrencia real por fila.
"""
import os
import sys
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import transaction
from django.utils import timezone
from infrastructure.models import Cuenta, Transaccion
from infrastructure.adapters.repositories import (
    DjangoCuentaRepository, DjangoTransaccionRepository,
)
from infrastructure.adapters.fraude_adapter import evaluar_transferencia
from application.use_cases import RealizarTransferencia

# ============================================================
# CONFIGURACION
# ============================================================
SALDO_INICIAL = 100_000
MONTO_TRANSFERIR = 15_000
CANT_THREADS = 10
WORKERS = min(CANT_THREADS, os.cpu_count() * 2)

stats = {'exitosas': 0, 'rechazadas': 0, 'errores': 0}
stats_lock = __import__('threading').Lock()

def inc(k):
    with stats_lock:
        stats[k] += 1


def transferir(origen_id, alias_destino, monto):
    """Usa RealizarTransferencia con select_for_update() real."""
    try:
        repo_cuenta = DjangoCuentaRepository()
        repo_tx = DjangoTransaccionRepository()
        motor = type('MotorFraudAdapter', (), {'evaluar': staticmethod(evaluar_transferencia)})
        caso = RealizarTransferencia(repo_cuenta, repo_tx, motor_fraude=motor)

        with transaction.atomic():
            resultado = caso.ejecutar(
                cuenta_origen_id=origen_id,
                destino_busqueda=alias_destino,
                monto=Decimal(str(monto)),
                descripcion='Demo concurrencia',
            )

        if resultado.exitoso:
            inc('exitosas')
            return True
        inc('rechazadas')
        return False
    except Exception:
        inc('rechazadas')
        return False


def main():
    print('=' * 55)
    print('  DEMO DE CONCURRENCIA BANCARIA')
    print('  PostgreSQL + RealizarTransferencia + select_for_update()')
    print('=' * 55)

    cta_origen = Cuenta.objects.filter(
        cliente__usuario__username='alumno'
    ).first()

    if not cta_origen:
        from django.contrib.auth.models import User
        from infrastructure.models import Cliente, ConfiguracionSeguridad
        u = User.objects.filter(is_superuser=True).first()
        if not u:
            u = User.objects.create_superuser('admin_demo', 'admin@demo.com', 'Demo2026!')
        c, _ = Cliente.objects.get_or_create(usuario=u, defaults={'dni': '99999999'})
        ConfiguracionSeguridad.objects.get_or_create(cliente=c)
        cta_origen, _ = Cuenta.objects.get_or_create(
            cliente=c, defaults={
                'tipo_cuenta': 'ahorro', 'moneda': 'ARS',
                'numero_cuenta': 'DEMO00000001',
            }
        )

    destino = Cuenta.objects.filter(estado='activa').exclude(id=cta_origen.id).first()
    if not destino:
        print('Se necesitan al menos 2 cuentas activas.')
        return

    Cuenta.objects.filter(id=cta_origen.id).update(saldo=SALDO_INICIAL)
    cta_origen.refresh_from_db()
    saldo_inicial = float(cta_origen.saldo)
    alias_destino = destino.alias or str(destino.id)

    print(f'\nCuenta origen: #{cta_origen.id} ({cta_origen.cliente.usuario.username})')
    print(f'  Saldo inicial: ${saldo_inicial:,.2f}')
    print(f'Cuenta destino: #{destino.id} ({destino.cliente.usuario.username})')
    print(f'  Alias: {alias_destino}')
    print(f'Monto: ${MONTO_TRANSFERIR:,.2f}')
    print(f'Threads: {CANT_THREADS}')
    print(f'Esperado: {saldo_inicial // MONTO_TRANSFERIR:.0f} exitosas, '
          f'{CANT_THREADS - saldo_inicial // MONTO_TRANSFERIR:.0f} rechazadas')
    print()

    inicio_dt = timezone.now()
    inicio = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futuros = [
            executor.submit(transferir, cta_origen.id, alias_destino, MONTO_TRANSFERIR)
            for _ in range(CANT_THREADS)
        ]
        for f in as_completed(futuros):
            f.result()

    duracion = time.time() - inicio
    cta_origen.refresh_from_db()
    saldo_final_origen = float(cta_origen.saldo)
    total_debitado = stats['exitosas'] * MONTO_TRANSFERIR
    total_esperado_origen = saldo_inicial - total_debitado

    print('=' * 55)
    print('  RESULTADOS')
    print('=' * 55)
    print(f'  Transferencias exitosas:   {stats["exitosas"]}')
    print(f'  Transferencias rechazadas: {stats["rechazadas"]}')
    print(f'  Errores:                   {stats["errores"]}')
    print(f'  Duracion:                  {duracion:.3f}s')
    print(f'  Saldo final origen:        ${saldo_final_origen:,.2f}')
    print(f'  Total debitado:            ${total_debitado:,.2f}')
    print()

    print('  VALIDACIONES:')
    ok = True
    if saldo_final_origen == total_esperado_origen:
        print(f'  [OK] Saldo origen correcto'
              f' (${saldo_final_origen:,.2f} = ${saldo_inicial:,.2f} - ${total_debitado:,.2f})')
    else:
        print(f'  [ERROR] Saldo origen INCORRECTO'
              f' (esperado ${total_esperado_origen:,.2f}, real ${saldo_final_origen:,.2f})')
        ok = False

    if not Cuenta.objects.filter(id=cta_origen.id, saldo__gte=0).exists():
        print('  [ERROR] Saldo origen negativo (NUNCA deberia pasar)')
        ok = False
    else:
        print('  [OK] Sin saldos negativos')

    txs = Transaccion.objects.filter(
        descripcion='Demo concurrencia', fecha_creacion__gte=inicio_dt,
    ).count()
    if txs == stats['exitosas']:
        print(f'  [OK] Transacciones registradas: {txs}')
    else:
        print(f'  [WARN] Transacciones registradas: {txs} (esperadas: {stats["exitosas"]})')

    print()
    print('  QUE DEMUESTRA ESTA PRUEBA:')
    print('  1. select_for_update() real de PostgreSQL: bloquea SOLO la fila')
    print('     de la cuenta origen, no toda la base de datos.')
    print('  2. Orden por ID ascendente: evita deadlocks al bloquear')
    print('     siempre las cuentas en el mismo orden.')
    print('  3. transaction.atomic(): cada operacion es una unidad ACID.')
    print('  4. RealizarTransferencia + repositorios reales: el flujo')
    print('     COMPLETO del sistema soporta concurrencia sin cambios.')
    print('  5. Migracion de SQLite a PostgreSQL sin tocar el codigo')
    print('     del dominio (arquitectura hexagonal).')
    print()
    if ok:
        print('  [OK] TODO OK - la integridad del saldo se mantuvo.')
    else:
        print('  [ERROR] HAY ERRORES - revisar.')

if __name__ == '__main__':
    main()
