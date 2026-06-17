# Banco Hexagonal — Sistema Bancario

Sistema bancario web con detección de fraude y scoring crediticio, desarrollado como proyecto académico con **Python + Django 6.0** y **arquitectura híbrida MTV + Hexagonal**.

## Funcionalidades

- **Registro de clientes** con datos personales (DNI, fecha de nacimiento, género, profesión, ingreso mensual, nivel educativo)
- **Inicio de sesión** seguro con contraseñas hasheadas (PBKDF2) y protección contra fuerza bruta
- **Panel personal** con saldo real, cuentas, alias, CVU, movimientos y préstamos activos
- **Transferencias bancarias** reales con concurrencia (`SELECT FOR UPDATE`, transacciones ACID)
- **Préstamos personales** — solicitud, simulación de cuotas (sistema francés o alemán), pago de cuotas
- **Alias y CVU** por cuenta — búsqueda en transferencias sin revelar el número de cuenta
- **Diseño responsive** (mobile, tablet, desktop) con accesibilidad WCAG 2.1 AA
- **Seguridad OWASP**: CSRF, XSS, SQL Injection, rate limiting, PCI DSS (sin almacenamiento de CVV)
- **Arquitectura hexagonal** implementada: dominio puro sin dependencias, puertos, adaptadores y casos de uso

## Tecnologías

| Tecnología | Uso |
|---|---|
| **Python 3.13** | Lenguaje principal |
| **Django 6.0** | Framework web (MTV para auth, hexagonal para lógica bancaria) |
| **PostgreSQL** | Base de datos (local o Neon Serverless) |
| **HTML5 + CSS3** | Frontend vanilla, sin frameworks externos |
| **docx (Node.js)** | Generación de informe IEEE 830 en formato Word |

## Requisitos

- Python 3.10+
- PostgreSQL

## Instalación

```bash
# 1. Clonar
git clone https://github.com/Danico19827/sistema_banco.git
cd sistema_banco

# 2. Entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env
# Editar .env con los datos de tu base de datos

# 5. Migraciones
python manage.py migrate

# 6. Iniciar
python manage.py runserver
```

Abrí `http://localhost:8000` en el navegador.

## Variables de entorno (`.env`)

```
SECRET_KEY=clave-secreta-de-django
DEBUG=True
DB_NAME=bancadb
DB_USER=usuario
DB_PASSWORD=contraseña
DB_HOST=localhost
DB_PORT=5432
```

Para generar `SECRET_KEY`:
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Rutas del sistema

| Ruta | Descripción |
|---|---|
| `/` | Landing page |
| `/registro/` | Crear cuenta nueva |
| `/inicio-sesion/` | Iniciar sesión |
| `/cerrar-sesion/` | Cerrar sesión |
| `/panel/` | Panel del cliente (saldos, cuentas, movimientos, préstamos) |
| `/transferencia/` | Nueva transferencia |
| `/prestamos/` | Lista de préstamos |
| `/prestamos/solicitar/` | Simular y solicitar préstamo |
| `/prestamos/<id>/` | Detalle del préstamo y pago de cuotas |

## Estructura del proyecto

```
Banco/
├── config/                  # Configuración de Django (settings, urls)
├── domain/                  # Capa de dominio hexagonal
│   ├── entities.py          #   Dataclases puras (sin Django)
│   ├── ports.py             #   Interfaces (RepositorioCuenta, etc.)
│   └── rules.py             #   Reglas de negocio: validación, simulación de cuotas
├── application/             # Casos de uso (orquestan domain + adapters)
│   └── use_cases.py         #   RealizarTransferencia, SolicitarPrestamo, PagarCuota
├── infrastructure/          # App Django (MTV + adaptadores)
│   ├── models.py            #   8 modelos (Cliente, Cuenta, Transaccion, Prestamo, etc.)
│   ├── auth_views.py        #   Vistas CBV (PanelView, TransferenciaView, PrestamoListView...)
│   ├── forms.py             #   Formulario de registro
│   ├── signals.py           #   Señal post_save (User → Cliente + Cuenta + Config)
│   ├── adapters/
│   │   └── repositories.py  #   DjangoCuentaRepository, DjangoPrestamoRepository
│   └── migrations/          #   Migraciones de base de datos
├── templates/               # Plantillas HTML
│   ├── base.html            #   Layout base (header, nav, footer, skip link)
│   ├── inicio.html          #   Landing page
│   ├── login.html           #   Inicio de sesión
│   ├── registro.html        #   Registro de cliente
│   ├── dashboard.html       #   Panel del cliente
│   ├── transferencia.html   #   Formulario de transferencia
│   ├── transferencia_exito.html
│   └── prestamos/           #   Vistas de préstamos
│       ├── lista.html
│       ├── solicitar.html
│       └── detalle.html
├── static/css/estilo.css    # Estilos CSS
└── pruebas/                 # Tests (unitarias, integración, concurrencia)
```

## Arquitectura

El proyecto combina **Django MTV** (registro, login, panel) con **Arquitectura Hexagonal** (transferencias, préstamos). La lógica de negocio está en `domain/rules.py` y `application/use_cases.py`, aislada del framework. Los adaptadores en `infrastructure/adapters/repositories.py` implementan las interfaces usando Django ORM con `select_for_update()` para concurrencia.

```
  Django View (MTV)    →    Caso de Uso    →    Puerto (Interface)    →    Adaptador (Django ORM)
  PanelView                   RealizarTransferencia   RepositorioCuenta         DjangoCuentaRepository
  TransferenciaView           SolicitarPrestamo       RepositorioPrestamo      DjangoPrestamoRepository
  PrestamoCrearView           PagarCuota
```

Desarrollado para la materia — Junio 2026.
