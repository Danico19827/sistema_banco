import os
import sys
import time
import random
import uuid
import unicodedata
from datetime import date, timedelta, datetime
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import User
from django.db import connection, transaction
from django.db.models import F, Q
from infrastructure.models import (
    Cliente, Cuenta, ConfiguracionSeguridad,
    Prestamo, CuotaPrestamo, PlazoFijo, Transaccion,
)

# ============================================================
# CONFIGURACIÓN
# ============================================================
TOTAL_USUARIOS = 500
BATCH_SIZE = 100
WORKERS = min(16, os.cpu_count() * 2)
PASSWORD = 'BancoHexagonal2026!'
LOG_FILE = os.path.join(os.path.dirname(__file__), 'usuarios_generados_masivo.txt')

GENERO_OPCIONES = ['M', 'F']
EDUCACION_OPCIONES = ['primario', 'secundario', 'terciario', 'universitario', 'posgrado']
PROFESIONES = ['Ingeniero', 'Docente', 'Médico', 'Abogado', 'Contador',
               'Arquitecto', 'Programador', 'Diseñador', 'Comerciante', 'Empleado']

TASA_PRESTAMO = 0.05
TASA_PLAZO_FIJO = 0.08
SALDO_MIN = 500_000
SALDO_MAX = 1_500_000
TRANSFER_MAX = 10
TRANSFER_MONTO_MIN = 100
TRANSFER_MONTO_MAX = 2_000

# ============================================================
# ESTADÍSTICAS
# ============================================================
stats = {
    'usuarios_creados': 0,
    'transferencias_exitosas': 0,
    'transferencias_fallidas': 0,
    'prestamos_creados': 0,
    'cuotas_pagadas': 0,
    'plazos_fijos_creados': 0,
    'plazos_fijos_cancelados': 0,
    'errores': 0,
}

stats_lock = __import__('threading').Lock()

def inc_stat(key, val=1):
    with stats_lock:
        stats[key] += val


# ============================================================
# CONFIGURAR SQLITE
# ============================================================
with connection.cursor() as c:
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA busy_timeout=10000')
    c.execute('PRAGMA cache_size=-64000')


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def generar_dni_usado(existentes):
    while True:
        dni = str(random.randint(10000000, 99999999))
        if dni not in existentes:
            existentes.add(dni)
            return dni

def limpiar_nombre(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return ''.join(c for c in texto if c.isalnum()).lower()

def generar_alias(first_name, last_name, username, existentes):
    if first_name and last_name:
        base = f"{limpiar_nombre(first_name)}.{limpiar_nombre(last_name)}"
    else:
        base = limpiar_nombre(username)
    sufijo = uuid.uuid4().hex[:4]
    alias = f"{base}.{sufijo}"[:20]
    if not alias.endswith(sufijo):
        alias = f"{base[:15]}.{sufijo}"[:20]
    while alias in existentes:
        sufijo = uuid.uuid4().hex[:4]
        alias = f"{base[:15]}.{sufijo}"[:20]
    existentes.add(alias)
    return alias

def generar_cvu(existentes):
    while True:
        cvu = '0' + str(uuid.uuid4().int % 10**21).zfill(21)
        if cvu not in existentes:
            existentes.add(cvu)
            return cvu

def generar_numero_cuenta(existentes):
    while True:
        nro = uuid.uuid4().hex[:12].upper()
        if nro not in existentes:
            existentes.add(nro)
            return nro


# ============================================================
# FASE 1: CREAR USUARIOS (ORM CON LOTES PARALELOS)
# ============================================================

def crear_lote_usuarios(inicio, fin, dnis_usados, aliases_usados, cvu_usados, nros_cuenta_usados):
    users_batch = []
    for i in range(inicio, fin):
        username = f'muser_{i}'
        first_name = f'Usuario{i}'
        last_name = f'Apellido{i}'
        u = User(username=username, first_name=first_name, last_name=last_name, email=f'{username}@example.com')
        u.set_password(PASSWORD)
        users_batch.append(u)

    created = User.objects.bulk_create(users_batch)

    clientes = []
    for u in created:
        clientes.append(Cliente(
            usuario=u,
            dni=generar_dni_usado(dnis_usados),
            telefono=f'11{random.randint(10000000,99999999)}',
            direccion=f'Calle {random.randint(1,9999)} N° {random.randint(100,9999)}',
            fecha_nacimiento=date(random.randint(1970, 2003), random.randint(1, 12), random.randint(1, 28)),
            genero=random.choice(GENERO_OPCIONES),
            profesion=random.choice(PROFESIONES),
            ingreso_mensual=Decimal(str(random.randint(20000, 200000))),
            nivel_educativo=random.choice(EDUCACION_OPCIONES),
            score_crediticio_inicial=random.randint(300, 800),
        ))

    Cliente.objects.bulk_create(clientes)

    cuentas = []
    configs = []
    for cli, u in zip(clientes, created):
        cuentas.append(Cuenta(
            cliente=cli, tipo_cuenta='ahorro',
            numero_cuenta=generar_numero_cuenta(nros_cuenta_usados),
            alias=generar_alias(u.first_name, u.last_name, u.username, aliases_usados),
            cvu=generar_cvu(cvu_usados),
            saldo=Decimal(str(random.randint(SALDO_MIN, SALDO_MAX))),
            moneda='ARS', estado='activa',
        ))
        configs.append(ConfiguracionSeguridad(cliente=cli))

    Cuenta.objects.bulk_create(cuentas)
    ConfiguracionSeguridad.objects.bulk_create(configs)

    return len(created)


def crear_usuarios():
    print(f'Creando {TOTAL_USUARIOS} usuarios con {WORKERS} workers...')
    inicio = time.time()

    existentes = {
        'dnis': set(Cliente.objects.values_list('dni', flat=True)),
        'aliases': set(Cuenta.objects.values_list('alias', flat=True)),
        'cvu': set(Cuenta.objects.values_list('cvu', flat=True)),
        'nros': set(Cuenta.objects.values_list('numero_cuenta', flat=True)),
    }
    dnis, aliases, cvu_set, nros = existentes['dnis'], existentes['aliases'], existentes['cvu'], existentes['nros']

    lotes = [(i, min(i + BATCH_SIZE, TOTAL_USUARIOS)) for i in range(0, TOTAL_USUARIOS, BATCH_SIZE)]

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futuros = [executor.submit(crear_lote_usuarios, i, f, dnis, aliases, cvu_set, nros) for i, f in lotes]
        for f in as_completed(futuros):
            inc_stat('usuarios_creados', f.result())

    print(f'  Creados: {stats["usuarios_creados"]} en {time.time()-inicio:.1f}s')


# ============================================================
# FASE 2: OPERACIONES CON USO DE F() ATOMICAS
# ============================================================

def transferir_f(cuenta_origen_id, cuenta_destino_id, monto):
    try:
        with transaction.atomic():
            ok = Cuenta.objects.filter(id=cuenta_origen_id, saldo__gte=monto).update(saldo=F('saldo') - monto)
            if not ok:
                inc_stat('transferencias_fallidas')
                return
            Cuenta.objects.filter(id=cuenta_destino_id).update(saldo=F('saldo') + monto)
            Transaccion.objects.create(
                tipo='transferencia', monto=monto,
                cuenta_origen_id=cuenta_origen_id, cuenta_destino_id=cuenta_destino_id,
                estado='completada',
                descripcion=f'Transferencia masiva #{cuenta_origen_id}->#{cuenta_destino_id}',
            )
        inc_stat('transferencias_exitosas')
    except Exception:
        inc_stat('errores')


def crear_prestamo_f(cliente_id, cuenta_id, monto, plazo, sistema):
    try:
        from domain.rules import simular_cuotas_frances, simular_cuotas_aleman
        prestamo = Prestamo.objects.create(
            cliente_id=cliente_id, monto_original=monto, saldo_pendiente=monto,
            tasa_interes_anual=TASA_PRESTAMO, plazo_meses=plazo,
            sistema_amortizacion=sistema, estado='activo',
        )
        cuotas_sim = (simular_cuotas_frances if sistema == 'frances' else simular_cuotas_aleman)(monto, TASA_PRESTAMO, plazo)
        hoy = date.today()
        for i, c in enumerate(cuotas_sim):
            vencimiento = date(hoy.year + (hoy.month + i) // 12, ((hoy.month + i - 1) % 12) + 1, 1)
            CuotaPrestamo.objects.create(
                prestamo_id=prestamo.id, numero_cuota=c.numero,
                monto_cuota=c.monto_cuota, fecha_vencimiento=vencimiento, estado='pendiente',
            )

        Cuenta.objects.filter(id=cuenta_id).update(saldo=F('saldo') + monto)
        Transaccion.objects.create(
            tipo='deposito', monto=monto, cuenta_destino_id=cuenta_id,
            estado='completada', descripcion=f'Préstamo #{prestamo.id} - Acreditación',
        )
        inc_stat('prestamos_creados')

        if random.random() < 0.60:
            cuotas = CuotaPrestamo.objects.filter(prestamo_id=prestamo.id).order_by('numero_cuota')[:3]
            for cuota in cuotas:
                ok = Cuenta.objects.filter(id=cuenta_id, saldo__gte=cuota.monto_cuota).update(saldo=F('saldo') - cuota.monto_cuota)
                if ok:
                    CuotaPrestamo.objects.filter(id=cuota.id).update(estado='pagada', fecha_pago=hoy, monto_pagado=cuota.monto_cuota)
                    inc_stat('cuotas_pagadas')
    except Exception:
        inc_stat('errores')


def crear_plazofijo_f(cuenta_id, monto, cliente_id, dias):
    try:
        ok = Cuenta.objects.filter(id=cuenta_id, saldo__gte=monto).update(saldo=F('saldo') - monto)
        if not ok:
            return
        vencimiento = date.today() + timedelta(days=dias)
        monto_venc = (monto + monto * Decimal(str(TASA_PLAZO_FIJO)) * Decimal(dias) / Decimal('365')).quantize(Decimal('0.01'))
        pf = PlazoFijo.objects.create(
            cliente_id=cliente_id, cuenta_id=cuenta_id, monto=monto,
            plazo_dias=dias, tasa_interes_anual=TASA_PLAZO_FIJO,
            monto_al_vencimiento=monto_venc, fecha_vencimiento=vencimiento, estado='activo',
        )
        Transaccion.objects.create(
            tipo='plazo_fijo', monto=monto, cuenta_origen_id=cuenta_id,
            estado='completada', descripcion=f'Constitución PF #{pf.id} - {dias} días',
        )
        inc_stat('plazos_fijos_creados')

        if random.random() < 0.30:
            time.sleep(random.uniform(0.001, 0.01))
            pf_db = PlazoFijo.objects.filter(id=pf.id, estado='activo').first()
            if pf_db and pf_db.fecha_constitucion:
                dias_trans = (date.today() - pf_db.fecha_constitucion.date()).days
                dias_dev = max(dias_trans, 0)
                interes = monto * Decimal(str(TASA_PLAZO_FIJO)) * Decimal(dias_dev) / Decimal('365')
                devolucion = monto + interes * Decimal('0.50')
                Cuenta.objects.filter(id=cuenta_id).update(saldo=F('saldo') + devolucion)
                PlazoFijo.objects.filter(id=pf.id).update(estado='cancelado')
                Transaccion.objects.create(
                    tipo='cancelacion_plazo_fijo', monto=devolucion, cuenta_destino_id=cuenta_id,
                    estado='completada', descripcion=f'Cancelación PF #{pf.id}',
                )
                inc_stat('plazos_fijos_cancelados')
    except Exception:
        inc_stat('errores')


def worker_operaciones(ops):
    for op in ops:
        try:
            tipo = op[0]
            if tipo == 'transferir':
                _, cta_origen, cta_dest, monto = op
                transferir_f(cta_origen, cta_dest, monto)
            elif tipo == 'prestamo_crear':
                _, cta_id, cli_id, monto, plazo, sistema = op
                crear_prestamo_f(cli_id, cta_id, monto, plazo, sistema)
            elif tipo == 'plazofijo_crear':
                _, cta_id, cli_id, monto, dias = op
                crear_plazofijo_f(cta_id, monto, cli_id, dias)
        except Exception:
            inc_stat('errores')


def generar_operaciones():
    print(f'Generando operaciones con {WORKERS} workers...')
    inicio = time.time()

    cuentas_todas = list(Cuenta.objects.filter(estado='activa').select_related('cliente__usuario'))

    todas_las_ops = []
    for cta in cuentas_todas:
        cli = cta.cliente
        ops_usuario = []

        destinos = [c for c in cuentas_todas if c.id != cta.id]
        if destinos:
            cant = min(TRANSFER_MAX, len(destinos))
            for dest in random.sample(destinos, cant):
                monto = Decimal(str(random.randint(TRANSFER_MONTO_MIN, TRANSFER_MONTO_MAX)))
                ops_usuario.append(('transferir', cta.id, dest.id, monto))

        if random.random() < 0.30:
            monto_p = Decimal(str(random.randint(10000, 200000)))
            plazo = random.choice([3, 6, 12, 18])
            sistema = random.choice(['frances', 'aleman'])
            ops_usuario.append(('prestamo_crear', cta.id, cli.id, monto_p, plazo, sistema))

        if random.random() < 0.20:
            monto_pf = Decimal(str(random.randint(50000, 300000)))
            dias = random.randint(30, 180)
            ops_usuario.append(('plazofijo_crear', cta.id, cli.id, monto_pf, dias))

        if ops_usuario:
            todas_las_ops.append(ops_usuario)

    random.shuffle(todas_las_ops)
    total_ops = sum(len(ops) for ops in todas_las_ops)
    print(f'  Total operaciones planificadas: {total_ops}')

    batch_ops = [[] for _ in range(WORKERS)]
    for i, ops in enumerate(todas_las_ops):
        batch_ops[i % WORKERS].extend(ops)

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futuros = [executor.submit(worker_operaciones, batch) for batch in batch_ops]
        for i, f in enumerate(as_completed(futuros)):
            f.result()
            if (i + 1) % 5 == 0:
                pct = (i + 1) / WORKERS * 100
                print(f'    Workers: {i+1}/{WORKERS} ({pct:.0f}%) | OK: {stats["transferencias_exitosas"]} | Saldo insuf: {stats["transferencias_fallidas"]} | Err: {stats["errores"]}')

    dur = time.time() - inicio
    print(f'  Completado en {dur:.1f}s')
    print(f'  Transferencias: {stats["transferencias_exitosas"]} OK / {stats["transferencias_fallidas"]} saldo insuficiente')
    print(f'  Préstamos: {stats["prestamos_creados"]} | Cuotas pagadas: {stats["cuotas_pagadas"]}')
    print(f'  Plazos fijos: {stats["plazos_fijos_creados"]} creados / {stats["plazos_fijos_cancelados"]} cancelados')
    if stats['errores']:
        print(f'  Errores inesperados: {stats["errores"]}')


# ============================================================
# FASE 3: LOG
# ============================================================

def escribir_log(inicio_time, fin_time):
    usuarios = User.objects.filter(username__startswith='muser_').order_by('username')
    duracion = fin_time - inicio_time
    minutos = int(duracion // 60)
    segundos = int(duracion % 60)
    duracion_str = f'{minutos}m {segundos}s' if minutos else f'{segundos:.2f}s'
    total_ops = sum(stats.values())
    throughput = total_ops / duracion if duracion > 0 else 0

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write('\n')
        f.write('=' * 60 + '\n\n')
        f.write('GENERACIÓN MASIVA DE DATOS\n')
        f.write(f'Inicio: {datetime.fromtimestamp(inicio_time).strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Fin: {datetime.fromtimestamp(fin_time).strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Duracion: {duracion_str}\n')
        f.write('=' * 60 + '\n\n')
        f.write('Parámetros:\n')
        f.write(f'  Usuarios: {TOTAL_USUARIOS}\n')
        f.write(f'  Workers: {WORKERS}\n')
        f.write(f'  Contraseña: {PASSWORD}\n')
        f.write(f'  Saldo inicial: ${SALDO_MIN:,} - ${SALDO_MAX:,}\n\n')
        f.write('Resultados:\n')
        f.write(f'  Usuarios creados: {stats["usuarios_creados"]}\n')
        f.write(f'  Transferencias OK: {stats["transferencias_exitosas"]}\n')
        f.write(f'  Transferencias saldo insuf.: {stats["transferencias_fallidas"]}\n')
        f.write(f'  Préstamos: {stats["prestamos_creados"]}\n')
        f.write(f'  Cuotas pagadas: {stats["cuotas_pagadas"]}\n')
        f.write(f'  Plazos fijos creados: {stats["plazos_fijos_creados"]}\n')
        f.write(f'  Plazos fijos cancelados: {stats["plazos_fijos_cancelados"]}\n')
        f.write(f'  Errores: {stats["errores"]}\n')
        f.write(f'  Total operaciones: {total_ops}\n')
        f.write(f'  Throughput: {throughput:.2f} ops/segundo\n\n')
        f.write(f'Usuarios para login (contraseña: {PASSWORD}):\n')
        f.write('=' * 60 + '\n')
        for u in usuarios:
            c = getattr(u, 'cliente', None)
            cta = c.cuentas.first() if c else None
            nro_cta = cta.numero_cuenta if cta else '?'
            saldo = f'${cta.saldo:,.2f}' if cta else '?'
            nombre = f'{u.first_name} {u.last_name}'.strip() or u.username
            f.write(f'{u.username:20s} | {nombre:25s} | Cta: {nro_cta:12s} | Saldo: {saldo:>12s}\n')
        f.write('=' * 60 + '\n\n')

    print(f'\nLog escrito en: {LOG_FILE}')
    print(f'  {usuarios.count()} usuarios listados')


# ============================================================
# MAIN
# ============================================================

def main():
    inicio_time = time.time()
    print('=' * 55)
    print('  GENERACIÓN MASIVA DE DATOS BANCARIOS')
    print(f'  Usuarios: {TOTAL_USUARIOS} | Workers: {WORKERS}')
    print(f'  Contraseña: {PASSWORD}')
    print(f'  Saldo: ${SALDO_MIN:,} - ${SALDO_MAX:,}')
    print('=' * 55)

    crear_usuarios()
    generar_operaciones()

    fin_time = time.time()
    escribir_log(inicio_time, fin_time)

    dur = fin_time - inicio_time
    print(f'\n¡Completado! Duración: {dur:.1f}s')
    print(f'Usuarios totales: {User.objects.count()}')


if __name__ == '__main__':
    main()
