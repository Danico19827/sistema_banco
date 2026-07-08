import os, sys, re, random, threading, time, json, argparse
from datetime import date, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

PASSWORD = 'Prueba_2026!'

LOG_FILE = os.path.join(os.path.dirname(__file__), 'registro_concurrente_log.txt')

nombres_m = ['Juan', 'Carlos', 'Luis', 'Diego', 'Martin', 'Pablo', 'Andres', 'Matias', 'Nicolas', 'Gabriel',
             'Federico', 'Alejandro', 'Fernando', 'Gustavo', 'Santiago', 'Lautaro', 'Ignacio', 'Emiliano',
             'Lucas', 'Franco', 'Agustin', 'Mauro', 'Hernan', 'Damian', 'Cristian']
nombres_f = ['Maria', 'Ana', 'Laura', 'Valentina', 'Camila', 'Lucia', 'Sofia', 'Florencia', 'Martina', 'Julieta',
             'Carolina', 'Rocio', 'Carla', 'Paula', 'Soledad', 'Veronica', 'Silvina', 'Gabriela', 'Daniela',
             'Victoria', 'Ludmila', 'Yamila', 'Belen', 'Ailen', 'Romina']
apellidos = ['Garcia', 'Rodriguez', 'Martinez', 'Lopez', 'Gonzalez', 'Perez', 'Fernandez', 'Diaz', 'Moreno',
             'Torres', 'Alvarez', 'Romero', 'Sosa', 'Castillo', 'Ramirez', 'Flores', 'Acosta', 'Medina',
             'Ruiz', 'Sanchez', 'Gimenez', 'Vega', 'Molina', 'Ortiz', 'Silva', 'Cruz', 'Rivas', 'Mansilla',
             'Pereyra', 'Lucero']
generos = ['M', 'F', 'N']
niveles_educativos = ['primario', 'secundario', 'terciario', 'universitario', 'posgrado']
profesiones = ['Docente', 'Ingeniero', 'Abogado', 'Medico', 'Contador', 'Comerciante', 'Empleado',
               'Programador', 'Arquitecto', 'Enfermero', 'Disenador', 'Electricista', 'Mecanico',
               'Estudiante', 'Jubilado', 'Administrativo', 'Vendedor', 'Cocinero', 'Chofer']

lock = threading.Lock()
next_idx = 0
exitosos = 0
fallidos = 0
errores_detalle: dict = {}


@dataclass
class PerfilRegistro:
    username: str
    first_name: str
    last_name: str
    email: str
    password1: str
    password2: str
    dni: str
    telefono: str
    direccion: str
    fecha_nacimiento: str
    genero: str
    profesion: str
    ingreso_mensual: str
    nivel_educativo: str


def generar_fecha_nac():
    inicio = date(1960, 1, 1)
    fin = date(2005, 12, 31)
    delta = fin - inicio
    d = inicio + timedelta(days=random.randint(0, delta.days))
    return d.strftime('%Y-%m-%d')


def generar_telefono():
    return f'11{random.randint(10000000, 99999999)}'


dnis_pool = set()


def generar_dni():
    while True:
        d = str(random.randint(1000000, 99999999))
        with lock:
            if d not in dnis_pool:
                dnis_pool.add(d)
                return d


def pre_generar_perfiles(cantidad):
    print(f'Pre-generando {cantidad} perfiles...')
    perfiles = []
    idx_username = 0
    for _ in range(cantidad):
        nombre = random.choice(nombres_m if random.random() < 0.5 else nombres_f)
        apellido = random.choice(apellidos)
        idx_username += 1
        username = f'{nombre.lower()}.{apellido.lower()}.{idx_username}'
        email = f'{username}@correo.com'
        dni = generar_dni()
        perfil = PerfilRegistro(
            username=username,
            first_name=nombre,
            last_name=apellido,
            email=email,
            password1=PASSWORD,
            password2=PASSWORD,
            dni=dni,
            telefono=generar_telefono(),
            direccion=f'Calle {random.randint(100, 9999)} Nro {random.randint(1, 9999)}',
            fecha_nacimiento=generar_fecha_nac(),
            genero=random.choice(generos),
            profesion=random.choice(profesiones),
            ingreso_mensual=str(random.randint(80000, 1500000)),
            nivel_educativo=random.choice(niveles_educativos),
        )
        perfiles.append(perfil)
        if (idx_username) % 2000 == 0:
            print(f'  {idx_username}/{cantidad} perfiles generados...')
    print(f'  {cantidad}/{cantidad} perfiles generados.')
    return perfiles


def extraer_csrf(html):
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    return match.group(1) if match else None


def registrar_usuario(perfil: PerfilRegistro, url_registro: str) -> tuple[bool, str]:
    session = requests.Session()
    try:
        resp_get = session.get(url_registro, timeout=10)
        if resp_get.status_code != 200:
            return False, f'GET status {resp_get.status_code}'

        csrf = extraer_csrf(resp_get.text)
        if not csrf:
            return False, 'No se pudo extraer CSRF'

        data = {
            'csrfmiddlewaretoken': csrf,
            'username': perfil.username,
            'first_name': perfil.first_name,
            'last_name': perfil.last_name,
            'email': perfil.email,
            'password1': perfil.password1,
            'password2': perfil.password2,
            'dni': perfil.dni,
            'telefono': perfil.telefono,
            'direccion': perfil.direccion,
            'fecha_nacimiento': perfil.fecha_nacimiento,
            'genero': perfil.genero,
            'profesion': perfil.profesion,
            'ingreso_mensual': perfil.ingreso_mensual,
            'nivel_educativo': perfil.nivel_educativo,
        }

        resp_post = session.post(url_registro, data=data, timeout=30, allow_redirects=False)

        if resp_post.status_code in (302, 303):
            return True, resp_post.headers.get('Location', '')
        else:
            errores = ''
            if b'error' in resp_post.content.lower() or b'class="error"' in resp_post.content.lower():
                match_err = re.search(r'class="errorlist"[^>]*>(.*?)</ul>', resp_post.text, re.DOTALL)
                if match_err:
                    errores = match_err.group(1)[:200]
                else:
                    match_err2 = re.search(r'<li[^>]*>(.*?)</li>', resp_post.text, re.DOTALL)
                    if match_err2:
                        errores = match_err2.group(1)[:200]
            return False, f'Status {resp_post.status_code}: {errores}'

    except requests.exceptions.ConnectionError:
        return False, 'Conexion rechazada - el servidor esta corriendo?'
    except Exception as e:
        return False, str(e)[:150]


def log_resultados(inicio, fin, cantidad, workers, url_registro):
    duracion = fin - inicio
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('REGISTRO MASIVO CONCURRENTE\n')
        f.write(f'Inicio: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(inicio))}\n')
        f.write(f'Fin: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(fin))}\n')
        f.write(f'Duracion: {duracion:.2f} segundos\n')
        f.write('=' * 60 + '\n\n')
        f.write(f'Workers: {workers}\n')
        f.write(f'Contrasena: {PASSWORD}\n')
        f.write(f'URL: {url_registro}\n\n')
        f.write(f'Intentados: {cantidad}\n')
        f.write(f'Exitosos: {exitosos}\n')
        f.write(f'Fallidos: {fallidos}\n')
        f.write(f'Throughput: {cantidad / duracion:.2f} usuarios/segundo\n\n')
        if errores_detalle:
            f.write('Detalle de errores:\n')
            for err, count in sorted(errores_detalle.items(), key=lambda x: -x[1]):
                f.write(f'  {count:>5}x - {err}\n')


def main():
    global next_idx, exitosos, fallidos, errores_detalle
    exitosos = 0
    fallidos = 0
    errores_detalle = {}

    parser = argparse.ArgumentParser(description='Registro masivo concurrente')
    parser.add_argument('--cantidad', type=int, default=10000, help='Cantidad de usuarios')
    parser.add_argument('--workers', type=int, default=20, help='Workers simultaneos')
    parser.add_argument('--server', type=str, default='http://127.0.0.1:8000', help='URL del servidor')
    args = parser.parse_args()

    cantidad = args.cantidad
    workers = args.workers
    server = args.server
    url_registro = f'{server}/registro/'

    print(f'Registro masivo concurrente - {cantidad} usuarios, {workers} workers')
    print(f'URL: {url_registro}')
    print(f'Contrasena comun: {PASSWORD}')
    print()

    perfiles = pre_generar_perfiles(cantidad)

    print(f'\nVerificando servidor en {server}...')
    try:
        r = requests.get(server, timeout=5)
        print(f'  Servidor OK (status {r.status_code})')
    except Exception as e:
        print(f'  ERROR: No se puede conectar al servidor: {e}')
        print('  Ejecutá primero: python manage.py runserver')
        return

    print(f'Iniciando registro concurrente con {workers} workers...\n')
    inicio = time.time()

    lote_size = max(1, cantidad // workers)
    lotes = [perfiles[i:i + lote_size] for i in range(0, len(perfiles), lote_size)]

    def tarea_worker_lote(lote):
        global exitosos, fallidos, errores_detalle
        for perfil in lote:
            ok, detalle = registrar_usuario(perfil, url_registro)
            with lock:
                if ok:
                    exitosos += 1
                else:
                    fallidos += 1
                    error_corto = detalle[:60]
                    errores_detalle[error_corto] = errores_detalle.get(error_corto, 0) + 1
            with lock:
                done = exitosos + fallidos
                if done % 500 == 0 or done == cantidad:
                    print(f'  Progreso: {done}/{cantidad} (exitosos: {exitosos}, fallidos: {fallidos})')

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futuros = [executor.submit(tarea_worker_lote, lote) for lote in lotes]
        for f in as_completed(futuros):
            f.result()

    fin = time.time()
    duracion = fin - inicio

    print(f'\nResultados finales:')
    print(f'  Duracion: {duracion:.2f} segundos')
    print(f'  Exitosos: {exitosos}')
    print(f'  Fallidos: {fallidos}')
    print(f'  Throughput: {cantidad / duracion:.2f} usuarios/segundo')
    if errores_detalle:
        print(f'\nErrores mas comunes:')
        for err, count in sorted(errores_detalle.items(), key=lambda x: -x[1])[:10]:
            print(f'  {count:>5}x - {err}')

    log_resultados(inicio, fin, cantidad, workers, url_registro)
    print(f'\nLog guardado en: {LOG_FILE}')


if __name__ == '__main__':
    main()
