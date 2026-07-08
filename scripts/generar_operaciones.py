"""
Generacion masiva de usuarios y operaciones bancarias.
Usa los COMPONENTES REALES del sistema:
- User.objects.create_user() + sennal post_save (creacion)
- RealizarTransferencia (transferencias + deteccion de fraude)
- SolicitarPrestamo (prestamos + scoring crediticio)
- PagarCuota (pago de cuotas)
- ConstituirPlazoFijo / CancelarPlazoFijo (plazos fijos)
"""
import os
import sys
import time
import random
import argparse
from datetime import date, datetime, timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import transaction
from django.db.models import F, Q
from django.contrib.auth.models import User
from infrastructure.models import Cliente, Cuenta, ConfiguracionSeguridad, Transaccion
from infrastructure.adapters.repositories import (
    DjangoCuentaRepository, DjangoTransaccionRepository,
    DjangoPrestamoRepository, DjangoPlazoFijoRepository,
)
from infrastructure.adapters.fraude_adapter import evaluar_transferencia
from infrastructure.adapters.scoring_adapter import evaluar_cliente
from application.use_cases import (
    RealizarTransferencia, SolicitarPrestamo, PagarCuota,
    ConstituirPlazoFijo, CancelarPlazoFijo,
)

# ============================================================
# CONFIG
# ============================================================
LOG_FILE = os.path.join(os.path.dirname(__file__), 'usuarios_generados_masivo.txt')
SALDO_MIN = 100_000
SALDO_MAX = 500_000
MONTO_TRANSFER_MIN = 500
MONTO_TRANSFER_MAX = 5_000
MONTO_PRESTAMO_MIN = 10_000
MONTO_PRESTAMO_MAX = 200_000
MONTO_PF_MIN = 50_000
MONTO_PF_MAX = 300_000
TASA_PRESTAMO = 0.05

stats = {
    'usuarios_creados': 0, 'depositos': 0,
    'transfers_ok': 0, 'transfers_fail': 0,
    'prestamos_ok': 0, 'prestamos_fail': 0,
    'cuotas_pagadas': 0, 'pf_creados': 0, 'pf_cancelados': 0,
    'errores': 0,
}
stats_lock = __import__('threading').Lock()
usuarios_log = []
log_lock = __import__('threading').Lock()


def inc(k, n=1):
    with stats_lock:
        stats[k] += n


def crear_lote(inicio, fin, password):
    """Crea usuarios usando User.objects.create_user() con sennal real."""
    ts = int(time.time())
    lotes_users = []
    for i in range(inicio, fin):
        username = f'gen_{ts}_{i}'
        first_name = f'Usuario{i}'
        last_name = f'Apellido{i}'
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=f'{username}@example.com',
            )
            lotes_users.append(user)
        except Exception:
            inc('errores')
    with log_lock:
        for u in lotes_users:
            c = getattr(u, 'cliente', None)
            cta = c.cuentas.first() if c else None
            usuarios_log.append({
                'username': u.username,
                'nombre': f'{u.first_name} {u.last_name}',
                'password': password,
                'cuenta': cta.numero_cuenta if cta else '?',
            })
    inc('usuarios_creados', len(lotes_users))
    return len(lotes_users)


def depositar_saldo():
    """Deposita saldo a cuentas con saldo $0."""
    ids = list(Cuenta.objects.filter(saldo=0, estado='activa').values_list('id', flat=True))
    if not ids:
        return 0
    from decimal import Decimal
    import random
    for cid in ids:
        saldo = Decimal(str(random.randint(SALDO_MIN, SALDO_MAX)))
        Cuenta.objects.filter(id=cid).update(saldo=saldo)
    inc('depositos', len(ids))
    return len(ids)


# ============================================================
# OPERACIONES (usando casos de uso reales)
# ============================================================

def transferir(origen_id, destino_busqueda, monto):
    """Usa RealizarTransferencia con deteccion de fraude."""
    try:
        repo_cuenta = DjangoCuentaRepository()
        repo_tx = DjangoTransaccionRepository()
        motor = type('MF', (), {'evaluar': staticmethod(evaluar_transferencia)})
        caso = RealizarTransferencia(repo_cuenta, repo_tx, motor_fraude=motor)
        with transaction.atomic():
            r = caso.ejecutar(origen_id, destino_busqueda, Decimal(str(monto)), '')
        if r.exitoso:
            inc('transfers_ok')
        else:
            inc('transfers_fail')
    except Exception:
        inc('transfers_fail')


def crear_prestamo(cliente_id, cuenta_id, monto, plazo, sistema):
    """Usa SolicitarPrestamo con scoring crediticio."""
    try:
        repo_p = DjangoPrestamoRepository()
        repo_c = DjangoCuentaRepository()
        motor = type('MS', (), {'evaluar': staticmethod(evaluar_cliente)})
        caso = SolicitarPrestamo(repo_p, repo_c, motor_scoring=motor)
        with transaction.atomic():
            prestamo, msg = caso.ejecutar(cliente_id, Decimal(str(monto)), plazo, sistema)
        if prestamo:
            repo_c.incrementar_saldo(cuenta_id, Decimal(str(monto)))
            inc('prestamos_ok')
            return prestamo
        inc('prestamos_fail')
        return None
    except Exception:
        inc('prestamos_fail')
        return None


def pagar_cuotas(prestamo_id, cuenta_id, cliente_id):
    """Usa PagarCuota para pagar hasta N cuotas."""
    try:
        from infrastructure.models import CuotaPrestamo
        repo_p = DjangoPrestamoRepository()
        repo_c = DjangoCuentaRepository()
        caso = PagarCuota(repo_p, repo_c)
        cuotas = CuotaPrestamo.objects.filter(
            prestamo_id=prestamo_id,
            estado__in=['pendiente', 'vencida'],
        ).order_by('numero_cuota')[:3]
        for cuota in cuotas:
            with transaction.atomic():
                ok, _ = caso.ejecutar(cuota.id, cuenta_id, cliente_id)
            if ok:
                inc('cuotas_pagadas')
    except Exception:
        pass


def crear_plazofijo(cliente_id, cuenta_id, monto, dias):
    """Usa ConstituirPlazoFijo."""
    try:
        repo_pf = DjangoPlazoFijoRepository()
        repo_c = DjangoCuentaRepository()
        caso = ConstituirPlazoFijo(repo_pf, repo_c)
        with transaction.atomic():
            pf, msg = caso.ejecutar(cliente_id, cuenta_id, Decimal(str(monto)), dias)
        if pf:
            inc('pf_creados')
            return pf
        return None
    except Exception:
        return None


def cancelar_plazofijo(pf_id, cliente_id):
    """Usa CancelarPlazoFijo."""
    try:
        repo_pf = DjangoPlazoFijoRepository()
        repo_c = DjangoCuentaRepository()
        caso = CancelarPlazoFijo(repo_pf, repo_c)
        ok, _ = caso.ejecutar(pf_id, cliente_id)
        if ok:
            inc('pf_cancelados')
    except Exception:
        pass


def worker_operaciones(cliente_id, cuenta_id, alias_destinos, prestamo_prob, pf_prob):
    """Genera operaciones para un usuario."""
    cuenta = Cuenta.objects.get(id=cuenta_id)
    if cuenta.saldo < 1000:
        return

    # Transferencias (5-10)
    cant_transfers = random.randint(5, 10)
    destinos = random.sample(alias_destinos, min(cant_transfers, len(alias_destinos)))
    for alias in destinos:
        monto = random.randint(MONTO_TRANSFER_MIN, MONTO_TRANSFER_MAX)
        transferir(cuenta_id, alias, monto)

    # Prestamo
    if random.random() < prestamo_prob:
        monto = random.randint(MONTO_PRESTAMO_MIN, MONTO_PRESTAMO_MAX)
        plazo = random.choice([6, 12, 18])
        sistema = random.choice(['frances', 'aleman'])
        p = crear_prestamo(cliente_id, cuenta_id, monto, plazo, sistema)
        if p and hasattr(p, 'id'):
            if random.random() < 0.6:
                pagar_cuotas(p.id, cuenta_id, cliente_id)

    # Plazo fijo
    if random.random() < pf_prob:
        monto = random.randint(MONTO_PF_MIN, MONTO_PF_MAX)
        dias = random.randint(30, 120)
        pf = crear_plazofijo(cliente_id, cuenta_id, monto, dias)
        if pf and random.random() < 0.3:
            cancelar_plazofijo(pf.id, cliente_id)


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Generar usuarios y operaciones')
    parser.add_argument('--crear', type=int, default=0, help='Crear N usuarios nuevos')
    parser.add_argument('--entre-si', action='store_true',
                        help='Operaciones solo entre los nuevos (requiere --crear)')
    parser.add_argument('--operaciones', action='store_true',
                        help='Ejecutar operaciones sobre usuarios existentes')
    parser.add_argument('--password', type=str, default='BancoHexagonal2026!')
    parser.add_argument('--workers', type=int, default=20)
    parser.add_argument('--prestamos', type=float, default=0.3, help='Probabilidad de prestamo')
    parser.add_argument('--plazos-fijos', type=float, default=0.2, help='Probabilidad de plazo fijo')
    args = parser.parse_args()

    if not args.crear and not args.operaciones:
        parser.print_help()
        print('\nError: Debes usar al menos --crear=N o --operaciones (o ambos).')
        sys.exit(1)

    workers = args.workers
    inicio = time.time()

    print('=' * 55)
    print('  GENERACION DE DATOS')
    print(f'  Workers: {workers}')
    if args.crear:
        print(f'  Crear usuarios: {args.crear}')
    if args.operaciones:
        print(f'  Operaciones: SI')
        print(f'  Entre los nuevos: {"SI" if args.entre_si else "NO (todos)"}')
        print(f'  Prob. prestamo: {args.prestamos}')
        print(f'  Prob. plazo fijo: {args.plazos_fijos}')
    print('=' * 55)

    # Crear usuarios
    if args.crear:
        print(f'\nCreando {args.crear} usuarios...')
        t0 = time.time()
        batch_size = 50
        lotes = [(i, min(i + batch_size, args.crear)) for i in range(0, args.crear, batch_size)]
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futuros = [ex.submit(crear_lote, i, f, args.password) for i, f in lotes]
            for f in as_completed(futuros):
                f.result()
        print(f'  Creados: {stats["usuarios_creados"]} en {time.time()-t0:.1f}s')

    # Operaciones
    if args.operaciones:
        # Determinar sobre que cuentas operar
        if args.crear and args.entre_si:
            usernames = [u['username'] for u in usuarios_log]
            qs = Cuenta.objects.filter(
                cliente__usuario__username__in=usernames,
                estado='activa',
            )
        else:
            qs = Cuenta.objects.filter(estado='activa')

        cuentas_con_saldo = list(qs.filter(saldo__gte=1000).select_related('cliente__usuario'))
        cuentas_sin_saldo = list(qs.filter(saldo=0))

        if cuentas_sin_saldo:
            print(f'\nDepositando saldo a {len(cuentas_sin_saldo)} cuentas en $0...')
            t0 = time.time()
            for c in cuentas_sin_saldo:
                Cuenta.objects.filter(id=c.id).update(
                    saldo=Decimal(str(random.randint(SALDO_MIN, SALDO_MAX)))
                )
            inc('depositos', len(cuentas_sin_saldo))
            print(f'  Depositados: {len(cuentas_sin_saldo)} en {time.time()-t0:.1f}s')
            cuentas_con_saldo = list(qs.filter(saldo__gte=1000).select_related('cliente__usuario'))

        if not cuentas_con_saldo:
            print('  No hay cuentas con saldo suficiente.')
            return

        print(f'\nGenerando operaciones sobre {len(cuentas_con_saldo)} cuentas...')
        t0 = time.time()

        alias_destinos = [c.alias or str(c.id) for c in cuentas_con_saldo]
        pf_prob = args.plazos_fijos
        tareas = [(c.cliente.id, c.id, alias_destinos, args.prestamos, pf_prob)
                  for c in cuentas_con_saldo]
        random.shuffle(tareas)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futuros = [ex.submit(worker_operaciones, *t) for t in tareas]
            for f in as_completed(futuros):
                f.result()

        print(f'  Operaciones completadas en {time.time()-t0:.1f}s')

    # Resultados
    duracion = time.time() - inicio
    print()
    print('=' * 55)
    print('  RESULTADOS')
    print('=' * 55)
    for k, v in stats.items():
        if v > 0:
            print(f'  {k}: {v}')
    print(f'  Duracion: {duracion:.1f}s')
    print()

    # Log
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write('\n')
        f.write('=' * 60 + '\n\n')
        f.write(f'GENERACION DE DATOS\n')
        f.write(f'Inicio: {datetime.fromtimestamp(inicio).strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Fin: {datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Duracion: {duracion:.1f}s\n')
        f.write('Flags:')
        if args.crear: f.write(f' --crear={args.crear}')
        if args.entre_si: f.write(f' --entre-si')
        if args.operaciones: f.write(f' --operaciones')
        f.write('\n')
        f.write('=' * 60 + '\n\n')
        f.write('Resultados:\n')
        for k, v in stats.items():
            if v > 0:
                f.write(f'  {k}: {v}\n')
        f.write('\n')
        if usuarios_log:
            f.write(f'Usuarios creados (contrasenha: {args.password}):\n')
            f.write('=' * 60 + '\n')
            for u in usuarios_log:
                f.write(f'{u["username"]:25s} | {u["nombre"]:25s} | Cta: {u["cuenta"]:12s}\n')
            f.write('=' * 60 + '\n\n')

    print(f'Log: {LOG_FILE}')

if __name__ == '__main__':
    main()
