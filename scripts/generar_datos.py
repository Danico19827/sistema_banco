import os, sys, random, uuid
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth.models import User
from infrastructure.models import Cliente, Cuenta, Transaccion, Prestamo, CuotaPrestamo
from django.db import transaction

CANTIDAD_CLIENTES = 100
PASSWORD = 'BancoHexagonal2026!'
LOG_FILE = os.path.join(os.path.dirname(__file__), 'usuarios_generados.txt')

nombres_m = ['Juan', 'Carlos', 'Luis', 'Diego', 'Martin', 'Pablo', 'Andres', 'Matias', 'Nicolas', 'Gabriel',
             'Federico', 'Alejandro', 'Fernando', 'Gustavo', 'Santiago', 'Lautaro', 'Ignacio', 'Emiliano',
             'Lucas', 'Franco', 'Agustin', 'Mauro', 'Hernan', 'Damian', 'Cristian']
nombres_f = ['María', 'Ana', 'Laura', 'Valentina', 'Camila', 'Lucia', 'Sofia', 'Florencia', 'Martina', 'Julieta',
             'Carolina', 'Rocio', 'Carla', 'Paula', 'Soledad', 'Veronica', 'Silvina', 'Gabriela', 'Daniela',
             'Victoria', 'Ludmila', 'Yamila', 'Belen', 'Ailen', 'Romina']
apellidos = ['Garcia', 'Rodriguez', 'Martinez', 'Lopez', 'Gonzalez', 'Perez', 'Fernandez', 'Diaz', 'Moreno',
             'Torres', 'Alvarez', 'Romero', 'Sosa', 'Castillo', 'Ramirez', 'Flores', 'Acosta', 'Medina',
             'Ruiz', 'Sanchez', 'Gimenez', 'Vega', 'Molina', 'Ortiz', 'Silva', 'Cruz', 'Rivas', 'Mansilla',
             'Pereyra', 'Lucero']
generos = ['M', 'F']
niveles_educativos = ['primario', 'secundario', 'terciario', 'universitario', 'posgrado']
profesiones = ['Docente', 'Ingeniero', 'Abogado', 'Medico', 'Contador', 'Comerciante', 'Empleado',
               'Programador', 'Arquitecto', 'Enfermero', 'Diseñador', 'Electricista', 'Mecanico',
               'Estudiante', 'Jubilado', 'Administrativo', 'Vendedor', 'Cocinero', 'Chofer']

def generar_dni_usado(existentes):
    while True:
        dni = str(random.randint(1000000, 99999999))
        if dni not in existentes:
            existentes.add(dni)
            return dni

def alias_desde_nombre(nombre, apellido):
    sufijo = uuid.uuid4().hex[:4].upper()
    return f'{nombre}.{apellido}.{sufijo}'.lower()

def generar_cvu():
    return '0' + str(random.randint(10**21 - 1, 10**22 - 1))

def generar_fecha_nac():
    inicio = date(1960, 1, 1)
    fin = date(2005, 12, 31)
    delta = fin - inicio
    return inicio + timedelta(days=random.randint(0, delta.days))

def generar_score():
    return random.randint(300, 800)

def crear_usuario(nombre, apellido, index):
    username = f'{nombre.lower()}.{apellido.lower()}{index}'
    email = f'{username}@email.com'
    user = User.objects.create_user(
        username=username,
        email=email,
        password=PASSWORD,
        first_name=nombre,
        last_name=apellido,
    )
    return user

def actualizar_cliente(cliente, dni, genero, fecha_nac, nivel_educativo, profesion, ingreso, score):
    cliente.dni = dni
    cliente.genero = genero
    cliente.fecha_nacimiento = fecha_nac
    cliente.nivel_educativo = nivel_educativo
    cliente.profesion = profesion
    cliente.ingreso_mensual = ingreso
    cliente.score_crediticio_inicial = score
    cliente.save()

def actualizar_cuenta(cuenta, alias, cvu, saldo):
    cuenta.alias = alias
    cuenta.cvu = cvu
    cuenta.saldo = saldo
    cuenta.save()

def crear_prestamo(cliente, monto, plazo_meses, tasa):
    prestamo = Prestamo.objects.create(
        cliente=cliente,
        monto_original=monto,
        saldo_pendiente=monto,
        tasa_interes_anual=tasa,
        plazo_meses=plazo_meses,
        sistema_amortizacion=random.choice(['frances', 'aleman']),
        estado='activo',
    )
    cuota_fija = (monto * Decimal(str(tasa / 12)) * (1 + Decimal(str(tasa / 12))) ** plazo_meses /
                  ((1 + Decimal(str(tasa / 12))) ** plazo_meses - 1))
    hoy = date.today()
    for i in range(plazo_meses):
        vto = date(hoy.year + (hoy.month + i) // 12, ((hoy.month + i - 1) % 12) + 1, 1)
        CuotaPrestamo.objects.create(
            prestamo=prestamo,
            numero_cuota=i + 1,
            monto_cuota=cuota_fija,
            fecha_vencimiento=vto,
            estado='pendiente',
        )
    return prestamo

def crear_transaccion(origen, destino, monto, desc):
    Transaccion.objects.create(
        tipo='transferencia',
        monto=monto,
        cuenta_origen=origen,
        cuenta_destino=destino,
        estado='completada',
        descripcion=desc,
    )

@transaction.atomic
def generar():
    print('Eliminando datos existentes...')
    CuotaPrestamo.objects.all().delete()
    Prestamo.objects.all().delete()
    Transaccion.objects.all().delete()
    Cuenta.objects.all().delete()
    Cliente.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete()

    dnis_existentes = set()
    usuarios_log = []

    print(f'Generando {CANTIDAD_CLIENTES} clientes...')
    for i in range(1, CANTIDAD_CLIENTES + 1):
        genero = random.choices(generos, weights=[0.48, 0.48])[0]
        nombre = random.choice(nombres_m if genero == 'M' else nombres_f)
        apellido = random.choice(apellidos)
        user = crear_usuario(nombre, apellido, i)
        cliente = user.cliente
        dni = generar_dni_usado(dnis_existentes)

        actualizar_cliente(
            cliente=cliente,
            dni=dni,
            genero=genero,
            fecha_nac=generar_fecha_nac(),
            nivel_educativo=random.choice(niveles_educativos),
            profesion=random.choice(profesiones),
            ingreso=Decimal(str(random.randint(80000, 1500000))),
            score=generar_score(),
        )

        cuenta = cliente.cuentas.first()
        actualizar_cuenta(
            cuenta=cuenta,
            alias=alias_desde_nombre(nombre, apellido),
            cvu=generar_cvu(),
            saldo=Decimal(str(random.randint(5000, 500000))),
        )

        if random.random() < 0.3:
            monto_p = Decimal(str(random.randint(10000, 200000)))
            plazo = random.randint(6, 36)
            crear_prestamo(cliente, monto_p, plazo, 0.05)

        usuarios_log.append(f'{user.username} | {PASSWORD} | {nombre} {apellido} | DNI {dni} | ${cuenta.saldo}')
        if i % 20 == 0:
            print(f'  {i}/{CANTIDAD_CLIENTES}...')

    print('Generando transacciones entre clientes...')
    cuentas = list(Cuenta.objects.all())
    random.shuffle(cuentas)
    for i in range(0, len(cuentas) - 1, 2):
        if i + 1 < len(cuentas):
            monto = Decimal(str(random.randint(100, min(50000, int(cuentas[i].saldo // 2)))))
            if monto > 0 and cuentas[i].saldo >= monto:
                cuentas[i].saldo -= monto
                cuentas[i].save()
                cuentas[i + 1].saldo += monto
                cuentas[i + 1].save()
                crear_transaccion(cuentas[i], cuentas[i + 1], monto, 'Transferencia por compra')
    print(f'  {len(cuentas)//2} transacciones creadas.')

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('USUARIOS GENERADOS\n')
        f.write('=' * 60 + '\n\n')
        for u in usuarios_log:
            f.write(u + '\n')
        f.write(f'\nTotal: {len(usuarios_log)} usuarios\n')
        f.write(f'Contrasena comun: {PASSWORD}\n')

    print(f'\nResumen:')
    print(f'  Usuarios: {User.objects.exclude(is_superuser=True).count()}')
    print(f'  Clientes: {Cliente.objects.count()}')
    print(f'  Cuentas: {Cuenta.objects.count()}')
    print(f'  Prestamos: {Prestamo.objects.count()}')
    print(f'  Cuotas: {CuotaPrestamo.objects.count()}')
    print(f'  Transacciones: {Transaccion.objects.count()}')
    print(f'\nUsuarios guardados en: {LOG_FILE}')
    print(f'Contrasena de todos: {PASSWORD}')

if __name__ == '__main__':
    generar()
