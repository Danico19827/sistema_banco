# 🏦 Banco - Sistema Bancario con Arquitectura Híbrida

Sistema bancario desarrollado como proyecto académico para demostrar:
- **Concurrencia** con bloqueos pesimistas (`select_for_update`)
- **Minería de Datos / ML** para detección de fraude
- **Seguridad OWASP** con autenticación robusta
- **Arquitectura Hexagonal + MTV** (híbrida pragmática)

## 📁 Estructura del proyecto

```
Banco/
├── config/                    # Configuración principal de Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── domain/                    # Capa de dominio (hexagonal puro)
│   ├── entities/              # Entidades de negocio (Cuenta, Transaccion)
│   ├── ports/                 # Puertos (interfaces abstractas)
│   └── reglas/                # Reglas de negocio (validaciones)
├── application/               # Casos de uso (orquestación)
├── infrastructure/            # App Django + Adaptadores
│   ├── adapters/              # Implementaciones concretas (ORM, ML)
│   ├── models.py              # Modelos ORM (Cliente, Cuenta, Transaccion)
│   ├── forms.py               # Formulario de registro extendido
│   ├── auth_views.py          # Vistas de autenticación (registro, login, inicio)
│   ├── views.py               # Vistas del core bancario
│   ├── container.py           # Contenedor de dependencias
│   └── apps.py                # Configuración de la app Django
├── ml_module/                 # Módulo de Minería de Datos (ML) (No implementado todavía)
├── pruebas/                   # Tests unitarios, integración y concurrencia
│   ├── unitarias/
│   ├── integracion/
│   └── concurrencia/
├── documentacion/             # Documentos (IEEE830, diagramas)
├── static/                    # Archivos estáticos (CSS, JS, imágenes)
│   └── css/
│       └── estilo.css         # Estilos compartidos entre plantillas
├── templates/                 # Plantillas HTML
│   ├── inicio.html            # Página de inicio / landing
│   ├── registro.html          # Página de registro de usuarios
│   └── login.html             # Página de login
├── manage.py                  # CLI de Django
├── requirements.txt
├── .env.example               # Variables de entorno de ejemplo
└── README.md
```

## 🧠 Arquitectura (filosofía)

El proyecto combina dos estilos arquitectónicos de forma pragmática:

| Módulo | Arquitectura | Justificación |
|--------|--------------|---------------|
| **Autenticación** (registro/login) | MTV clásico de Django | Aprovecha seguridad probada: hash de contraseñas, CSRF, sesiones. |
| **Core bancario** (transferencias) | Hexagonal (Puertos y Adaptadores) | Aísla la lógica crítica de concurrencia y permite pruebas unitarias con mocks. |
| **Detección de fraude** (ML) | Adaptador hexagonal | Intercambia modelos (Scikit-learn ↔ PyTorch) sin tocar la lógica de negocio. |

## 📦 Requisitos previos

- **Python 3.10+**
- **PostgreSQL** instalado y corriendo
- **Git** (opcional, para clonar)

## ⚙️ Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/Danico19827/sistema_banco.git
cd Banco
```

### 2. Crear entorno virtual y activarlo

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y personaliza:

```bash
cp .env.example .env
```

Luego edita `.env` con tus datos:

```
SECRET_KEY=genera-tu-propia-clave-aqui
DEBUG=True
DB_NAME=bancadb
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_HOST=tu_host_o_localhost
DB_PORT=5432
```

**Nota**: La configuración usa **Neon** por defecto. Para desarrollo local con PostgreSQL:
  - Cambiar `DB_HOST` a `localhost`
  - Asegúrate de que PostgreSQL esté corriendo

**Para generar tu SECRET_KEY:**
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Crear la base de datos PostgreSQL

```bash
sudo -u postgres createdb bancadb   # Linux
# En Windows, usar pgAdmin o el comando createdb desde la carpeta bin de PostgreSQL
```

### 6. Ejecutar migraciones

```bash
python manage.py makemigrations infrastructure
python manage.py migrate
```

Esto crea todas las tablas necesarias, incluyendo las del sistema de autenticación de Django.

## 🌍 Configuración regional

El proyecto está configurado para:
- **Idioma**: Español (Argentina)
- **Zona horaria**: `America/Argentina/Buenos_Aires`

Estos parámetros se configuran automáticamente en `config/settings.py`:

```python
LANGUAGE_CODE = 'es-AR'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
```

## 🎨 Estilos y plantillas

Los estilos CSS están centralizados en `static/css/estilo.css` y se comparten entre todas las plantillas HTML.

### Página de inicio (`templates/inicio.html`)
Landing page que muestra:
- Descripción del sistema
- Enlaces a Login y Registro
- Cumplimiento con WCAG 2.1 AA y pautas OWASP

## 🧩 Explicación del código (módulo de login/registro)

### Modelos (`infrastructure/models.py`)

```python
class Cliente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='activo')
```

- **User**: Modelo nativo de Django que maneja username, password (hasheada con PBKDF2), email, permisos, etc.
- **Cliente**: Extiende el User con teléfono, dirección y estado. Relación uno a uno.
- **`auto_now_add`** en `fecha_registro` establece la fecha automáticamente al crear el registro.

### Formulario de registro (`infrastructure/forms.py`)

```python
class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    telefono = forms.CharField(max_length=20)
    direccion = forms.CharField(widget=forms.Textarea)
```

- Hereda de **UserCreationForm** (seguridad incluida: hash, validación de contraseñas).
- Agrega campos extra que se guardan tanto en `User` como en `Cliente`.
- El método `save()` está sobrescrito para crear ambos registros en una sola transacción.

### Vistas de autenticación (`infrastructure/auth_views.py`)

#### Vista de inicio
```python
def inicio(request):
    return render(request, 'inicio.html')
```

#### Vista de registro
```python
def registro(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                usuario = form.save()
            login(request, usuario)
            return redirect('inicio')
    else:
        form = RegistroClienteForm()
    return render(request, 'registro.html', {'form': form})
```

- **`transaction.atomic()`** garantiza que User y Cliente se creen juntos o ninguno (ACID).
- **`login()`** crea la sesión segura automáticamente.
- **Vista de inicio** proporciona un landing page central.

### Plantillas HTML (`templates/`)

- Diseño **minimalista y profesional** con CSS puro.
- Protección **CSRF** incluida con `{% csrf_token %}`.
- Muestra errores de validación de forma elegante.

### URLs (`config/urls.py`)

```python
urlpatterns = [
    path('', inicio, name='inicio'),              # Landing page
    path('registro/', registro, name='registro'),  # Registro de nuevos usuarios
    path('login/', login_view, name='login'),      # Login de usuarios existentes
]
```

## 🚀 Ejecutar el proyecto

```bash
python manage.py runserver
```

Luego visitá en tu navegador:

- **Inicio**: http://localhost:8000/
- **Registro**: http://localhost:8000/registro/
- **Login**: http://localhost:8000/login/

### Flujo de uso
1. Entrás a `/` (landing page).
2. Podés crear una cuenta en `/registro/` con todos los datos.
3. Después del registro, quedás logueado y redirigido.
4. En `/login/` podés iniciar sesión con cuentas existentes.

## 🔒 Seguridad implementada

- Contraseñas **hasheadas** con PBKDF2 (Django)
- Protección **CSRF** en todos los formularios
- **XSS** mitigado por escape automático en templates
- **SQL Injection** bloqueado por el ORM de Django
- Sesiones seguras con cookies firmadas

## 📝 Próximos pasos

- Dashboard con saldo de cuenta y historial de transacciones
- Transferencias entre cuentas con bloqueo pesimista (`select_for_update`)
- Motor de fraude con Machine Learning integrado
- Pruebas de concurrencia con Locust
- Módulo de reporte de transacciones

## 👥 Para el equipo

Cada desarrollador debe:
1. Generar su propia `SECRET_KEY`
2. Configurar su `.env` local (sin subirlo a Git)
3. Tener PostgreSQL corriendo localmente con la base `bancadb` creada

El archivo `.env.example` sirve como guía de las variables necesarias.
