# Banco Hexagonal — Sistema Bancario

Sistema bancario web con **detección de fraude** (Isolation Forest) y **scoring crediticio** (Random Forest), desarrollado como proyecto académico con **Python + Django 6.0** y **arquitectura híbrida MTV + Hexagonal**.

## Estado de los Requisitos Funcionales

| RF | Nombre | Estado |
|---|---|---|
| RF-01 | Registro de Cliente | ✅ |
| RF-02 | Inicio de Sesión | ✅ |
| RF-03 | Página de Inicio Pública | ✅ |
| RF-04 | Consulta de Saldo (Dashboard) | ✅ |
| RF-05 | Transferencia Bancaria | ✅ |
| RF-06 | Historial de Movimientos | ✅ |
| RF-07 | Detección de Fraude con ML | ✅ |
| RF-08 | Autenticación 2FA | ❌ Pendiente |
| RF-09 | Gestión de Alias y CVU | ✅ |
| RF-10 | Solicitud de Préstamo | ✅ |
| RF-11 | Simulación y Plan de Pagos | ✅ |
| RF-12 | Gestión de Cuotas + Débito Automático | ✅ |
| RF-13 | Constitución de Plazo Fijo | ✅ |
| RF-14 | Cancelación Anticipada Plazo Fijo | ✅ |
| RF-15 | Scoring Crediticio con ML | ✅ |

## Funcionalidades destacadas

- **Registro de clientes** con datos personales (DNI, fecha de nacimiento, género, profesión, ingreso mensual, nivel educativo)
- **Inicio de sesión** seguro con contraseñas hasheadas (PBKDF2) y protección contra fuerza bruta (3 intentos → 15 min bloqueo)
- **Panel personal** con saldo real, cuentas, alias, CVU, movimientos y préstamos activos
- **Transferencias bancarias** reales con concurrencia (`SELECT FOR UPDATE` con orden por ID, transacciones ACID)
- **Detección de fraude en tiempo real** — cada transferencia evaluada con Isolation Forest (97.3% accuracy)
- **Préstamos personales** — solicitud con scoring crediticio ML (Random Forest, 97.8% accuracy), simulación de cuotas (sistema francés o alemán), pago de cuotas con débito automático opcional
- **Plazos fijos** — constitución con 8% TNA, cancelación anticipada con penalización prorrateada
- **Historial de movimientos** con paginación y filtros por tipo/fecha
- **Panel de métricas** (superusuario) con 4 gráficos Chart.js: burbujas (edad vs préstamos), torta (género), área (educación), gauge (score crediticio)
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
| `/panel/` | Panel del cliente (saldos, cuentas, movimientos, préstamos, plazos fijos) |
| `/transferencia/` | Nueva transferencia (con detección de fraude ML) |
| `/historial/` | Historial de movimientos con filtros y paginación |
| `/prestamos/` | Lista de préstamos |
| `/prestamos/solicitar/` | Simular y solicitar préstamo (con scoring crediticio ML) |
| `/prestamos/<id>/` | Detalle del préstamo y pago de cuotas |
| `/plazos-fijos/` | Lista de plazos fijos |
| `/plazos-fijos/constituir/` | Constituir nuevo plazo fijo |
| `/plazos-fijos/<id>/cancelar/` | Cancelar plazo fijo (POST) |
| `/depositar/` | Depositar dinero en tu cuenta |
| `/metricas/` | Panel de minería de datos (solo superusuario) |
| `/admin/` | Admin de Django |

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
│   ├── models.py            #   9 modelos (Cliente, Cuenta, Transaccion, Prestamo, etc.)
│   ├── auth_views.py        #   Vistas CBV (PanelView, TransferenciaView, HistorialView, ...)
│   ├── forms.py             #   Formulario de registro
│   ├── signals.py           #   Señal post_save (User → Cliente + Cuenta + Config)
│   ├── admin.py             #   Registro de modelos en admin Django
│   ├── adapters/
│   │   ├── repositories.py  #   DjangoCuentaRepository, DjangoPrestamoRepository
│   │   ├── modelo_fraude.pkl       # Modelo Isolation Forest serializado
│   │   ├── fraude_adapter.py       # Adaptador de detección de fraude
│   │   ├── modelo_scoring.pkl      # Modelo Random Forest serializado
│   │   └── scoring_adapter.py      # Adaptador de scoring crediticio
│   ├── management/commands/
│   │   └── pagar_cuotas_vencidas.py  # Débito automático de cuotas
│   └── migrations/          #   Migraciones de base de datos (0001-0007)
├── templates/               # Plantillas HTML
│   ├── base.html            #   Layout base (header, nav, footer, skip link)
│   ├── inicio.html          #   Landing page
│   ├── login.html           #   Inicio de sesión
│   ├── registro.html        #   Registro de cliente
│   ├── dashboard.html       #   Panel del cliente
│   ├── transferencia.html   #   Formulario de transferencia
│   ├── historial.html       #   Historial de movimientos con filtros
│   ├── metricas.html        #   Panel de minería de datos (superuser)
│   ├── depositar.html       #   Depósito en cuenta propia
│   ├── prestamos/           #   Vistas de préstamos
│   │   ├── lista.html
│   │   ├── solicitar.html
│   │   └── detalle.html
│   └── plazofijo/
│       ├── lista.html
│       └── crear.html
├── static/
│   ├── css/estilo.css       #   Estilos CSS del sistema
│   └── js/
│       ├── currency.js      #   Formateo de inputs monetarios
│       ├── prestamo_calc.js #   Cálculo en vivo de cuotas
│       ├── plazofijo_calc.js#   Cálculo en vivo de plazos fijos
│       └── charts_metricas.js #   Gráficos Chart.js para métricas
├── scripts/                 # Scripts auxiliares
│   ├── generar_datos.py          #  100 usuarios de prueba
│   ├── generar_masivo.py         #  500 usuarios + 6000+ transferencias concurrentes
│   ├── entrenar_fraude.py        #  Entrenamiento Isolation Forest (RF-07)
│   ├── entrenar_scoring.py       #  Entrenamiento Random Forest (RF-15)
│   ├── registro_masivo_concurrente.py
│   └── simular_transacciones.py
├── documentation/
│   ├── DOCUMENTACION.md    # Documentación didáctica detallada
│   └── IEEE830_v2.pdf      # Especificación IEEE 830
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
