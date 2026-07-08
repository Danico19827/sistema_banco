"""
Crea usuarios mediante HTTP contra /registro/.
Usa ThreadPoolExecutor para concurrencia real.
Pasa por todo el stack: middleware, CSRF, formularios, ORM, sennales.
Los datos se anexan al log sin sobrescribir los de ejecuciones anteriores.
"""
import os
import sys
import time
import random
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ============================================================
# CONFIGURACION
# ============================================================
URL_BASE = 'http://127.0.0.1:8000'
PASSWORD_DEFECTO = 'BancoHexagonal2026!'
WORKERS = 20

LOG_FILE = os.path.join(os.path.dirname(__file__), 'usuarios_generados_masivo.txt')

GENEROS = ['M', 'F']
EDUCACION = ['primario', 'secundario', 'terciario', 'universitario', 'posgrado']
PROFESIONES = ['Ingeniero', 'Docente', 'Medico', 'Abogado', 'Contador',
               'Arquitecto', 'Programador', 'Disenador', 'Comerciante', 'Empleado']

stats = {'exitosos': 0, 'fallidos': 0, 'errores': 0}
stats_lock = __import__('threading').Lock()
usuarios_creados = []
usuarios_lock = __import__('threading').Lock()


def inc(k):
    with stats_lock:
        stats[k] += 1


def registrar_usuario(i, password, url_base):
    """Registra un usuario via HTTP contra /registro/."""
    username = f'user_{int(time.time()*1000)}_{i}'
    first_name = f'Nombre{i}'
    last_name = f'Apellido{i}'
    dni = str(random.randint(10000000, 99999999))
    genero = random.choice(GENEROS)
    educacion = random.choice(EDUCACION)
    profesion = random.choice(PROFESIONES)
    ingreso = random.randint(20000, 200000)

    data = {
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'email': f'{username}@example.com',
        'password1': password,
        'password2': password,
        'dni': dni,
        'telefono': f'11{random.randint(10000000, 99999999)}',
        'direccion': f'Calle {random.randint(1,9999)} N° {random.randint(100,9999)}',
        'genero': genero,
        'fecha_nacimiento': f'{random.randint(1970, 2003)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
        'profesion': profesion,
        'ingreso_mensual': str(ingreso),
        'nivel_educativo': educacion,
    }

    try:
        session = requests.Session()
        resp_get = session.get(f'{url_base}/registro/', timeout=10)
        if resp_get.status_code != 200:
            inc('errores')
            return

        import re
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp_get.text)
        csrf_token = match.group(1) if match else ''

        data['csrfmiddlewaretoken'] = csrf_token
        resp = session.post(f'{url_base}/registro/', data=data, timeout=10)

        if resp.status_code in (200, 302):
            inc('exitosos')
            with usuarios_lock:
                usuarios_creados.append({
                    'username': username,
                    'nombre': f'{first_name} {last_name}',
                    'password': password,
                    'dni': dni,
                })
        else:
            inc('fallidos')
    except Exception:
        inc('errores')


def main():
    parser = argparse.ArgumentParser(description='Crear usuarios via HTTP')
    parser.add_argument('--usuarios', type=int, default=50, help='Cantidad de usuarios')
    parser.add_argument('--password', type=str, default='BancoHexagonal2026!', help='Contrasenha')
    parser.add_argument('--workers', type=int, default=20, help='Workers concurrentes')
    parser.add_argument('--url', type=str, default='http://127.0.0.1:8000', help='URL base')
    args = parser.parse_args()

    url_base = args.url
    password = args.password
    workers = args.workers

    print('=' * 55)
    print('  CREACION DE USUARIOS VIA HTTP')
    print(f'  Usuarios: {args.usuarios} | Workers: {workers}')
    print(f'  URL: {url_base}')
    print(f'  Contrasenha: {password}')
    print('=' * 55)

    inicio = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futuros = [
            executor.submit(registrar_usuario, i, password, url_base)
            for i in range(args.usuarios)
        ]
        for f in as_completed(futuros):
            f.result()

    fin = time.time()
    duracion = fin - inicio
    throughput = stats['exitosos'] / duracion if duracion > 0 else 0

    print()
    print(f'  Exitosos: {stats["exitosos"]}')
    print(f'  Fallidos: {stats["fallidos"]}')
    print(f'  Errores:  {stats["errores"]}')
    print(f'  Duracion: {duracion:.2f}s')
    print(f'  Throughput: {throughput:.2f} usuarios/s')
    print()

    # Escribir log (append)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write('\n')
        f.write('=' * 60 + '\n\n')
        f.write('CREACION DE USUARIOS VIA HTTP\n')
        f.write(f'Inicio: {datetime.fromtimestamp(inicio).strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Fin: {datetime.fromtimestamp(fin).strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Duracion: {duracion:.2f}s\n')
        f.write('=' * 60 + '\n\n')
        f.write('Parametros:\n')
        f.write(f'  Usuarios solicitados: {args.usuarios}\n')
        f.write(f'  Workers: {workers}\n')
        f.write(f'  URL: {url_base}\n')
        f.write(f'  Contrasenha: {password}\n\n')
        f.write('Resultados:\n')
        f.write(f'  Exitosos: {stats["exitosos"]}\n')
        f.write(f'  Fallidos: {stats["fallidos"]}\n')
        f.write(f'  Errores: {stats["errores"]}\n')
        f.write(f'  Throughput: {throughput:.2f} usuarios/segundo\n\n')
        f.write('Usuarios creados:\n')
        f.write('=' * 60 + '\n')
        for u in usuarios_creados:
            f.write(f'{u["username"]:25s} | {u["nombre"]:25s} | {password}\n')
        f.write('=' * 60 + '\n\n')

    print(f'Log escrito en: {LOG_FILE}')
    print(f'  {len(usuarios_creados)} usuarios listados')


if __name__ == '__main__':
    main()
