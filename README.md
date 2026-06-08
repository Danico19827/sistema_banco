# 🏦 Banco Hexagonal - Sistema Bancario

Sistema bancario web desarrollado como proyecto académico con **Python + Django**.

## Funcionalidades

- **Registro de clientes** con datos personales (DNI, teléfono, dirección, etc.)
- **Inicio de sesión** seguro con contraseñas hasheadas
- **Dashboard** con resumen de cuentas y movimientos
- **Simulación de transferencias** entre cuentas
- **Diseño responsive** adaptable a celulares y tablets
- **Módulo de alertas y fraude** preparado para Machine Learning

## Tecnologías

| Tecnología | Versión | Uso |
|-------------|---------|-----|
| Python | 3.13 | Lenguaje principal |
| Django | 6.0 | Framework web |
| PostgreSQL | - | Base de datos |
| HTML + CSS | - | Frontend (sin frameworks externos) |

## Requisitos

- Python 3.10+
- PostgreSQL instalado y corriendo

## Instalación rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/Danico19827/sistema_banco.git
cd sistema_banco

# 2. Crear entorno virtual
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus datos de base de datos

# 5. Crear la base de datos
createdb bancadb

# 6. Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# 7. Iniciar el servidor
python manage.py runserver
```

Listo. Abrí http://localhost:8000/ en tu navegador.

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

Para generar tu `SECRET_KEY`:
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Rutas del sistema

| Ruta | Descripción |
|------|-------------|
| `/` | Landing page |
| `/registro/` | Crear cuenta nueva |
| `/login/` | Iniciar sesión |
| `/logout/` | Cerrar sesión |
| `/dashboard/` | Panel del cliente |
| `/transferencia/` | Nueva transferencia |

## Estructura del proyecto

```
Banco/
├── config/              # Configuración de Django
├── domain/              # Capa de dominio (preparada para hexagonal)
├── infrastructure/      # App principal (modelos, vistas, formularios)
│   ├── models.py        # Modelos de base de datos
│   ├── forms.py         # Formulario de registro
│   ├── auth_views.py    # Vistas de autenticación y dashboard
│   └── adapters/        # Adaptadores hexagonales
├── templates/           # Plantillas HTML
├── static/              # Archivos CSS
└── pruebas/             # Tests
```

## Arquitectura

El proyecto combina **Django MTV** (para autenticación, que ya viene auditada) con **Arquitectura Hexagonal** (para la lógica bancaria, facilitando pruebas y cambios de base de datos).

Desarrollado para la materia — Junio 2026.
