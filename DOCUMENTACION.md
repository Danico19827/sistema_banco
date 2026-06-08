# Documentación del Sistema Bancario

> Proyecto académico — Materia: [Nombre de la materia]  
> Arquitectura: Híbrido (Hexagonal + MTV)  
> Tecnologías: Python, Django 6.0, PostgreSQL

---

## Índice

1. [¿Qué es este sistema?](#1-qué-es-este-sistema)
2. [Mapa del proyecto](#2-mapa-del-proyecto)
3. [El ciclo de vida de una solicitud](#3-el-ciclo-de-vida-de-una-solicitud-request)
4. [Las URLs del sistema](#4-las-urls-del-sistema)
5. [Las Vistas (Class-Based Views)](#5-las-vistas-class-based-views)
6. [Las Plantillas (Templates)](#6-las-plantillas-templates)
7. [Los Modelos (Base de datos)](#7-los-modelos-base-de-datos)
8. [El Formulario de Registro](#8-el-formulario-de-registro)
9. [Las Señales (Signals)](#9-las-señales-signals)
10. [Mensajes Flash](#10-mensajes-flash)
11. [Datos Mock](#11-datos-mock-de-mentira)
12. [Arquitectura: Híbrido Hexagonal + MTV](#12-arquitectura-híbrido-hexagonal--mtv)
13. [Glosario Django](#13-glosario-django)

---

## 1. ¿Qué es este sistema?

Es un **sistema bancario web** desarrollado como proyecto académico. Permite:

- Registrarse como cliente del banco
- Iniciar sesión
- Ver un panel con cuentas y movimientos
- Simular transferencias entre cuentas

### Tecnologías usadas

| Tecnología | Versión | ¿Para qué? |
|---|---|---|
| **Python** | 3.13 | Lenguaje de programación principal |
| **Django** | 6.0 | Framework web (gestiona rutas, base de datos, formularios, seguridad) |
| **PostgreSQL** | — | Base de datos (almacena usuarios, cuentas, transacciones) |
| **CSS (puro)** | — | Estilo visual de las páginas (sin frameworks externos) |
| **HTML + DTL** | — | Plantillas con el lenguaje de templates de Django |

---

## 2. Mapa del proyecto

```
Banco/
├── config/                  # Configuración principal de Django
│   ├── settings.py          #  Configuración global:
│   │                        #   - Apps instaladas
│   │                        #   - Conexión a la base de datos
│   │                        #   - Rutas de archivos estáticos
│   │                        #   - Zona horaria (Argentina)
│   ├── urls.py              #  Tabla de rutas del sitio
│   │                        #   Vincula cada URL con su Vista
│   ├── wsgi.py / asgi.py    #  Para publicar el sitio en internet
│
├── domain/                  #  Capa de dominio (Hexagonal)
│   ├── entities/            #   Entidades de negocio puras (vacíos)
│   ├── ports/               #   Interfaces abstractas (vacíos)
│   └── reglas/              #   Reglas de negocio (vacíos)
│   ── ── ── ── ──          #   Por ahora solo estructura
│
├── application/             #  Casos de uso (Hexagonal)
│   ── ── ── ── ──          #   Vacío, se implementará después
│
├── infrastructure/          #  App Django principal
│   ├── models.py            #   Modelos de base de datos
│   │                        #   (Cliente, Cuenta, Transaccion,
│   │                        #    Tarjeta, Prestamo, CuotaPrestamo,
│   │                        #    ConfiguracionSeguridad, AlertaFraude)
│   ├── forms.py             #   Formulario de registro de clientes
│   ├── auth_views.py        #   Vistas (login, registro, dashboard, etc.)
│   ├── signals.py           #   Señales (crear Cliente al crear User)
│   ├── app.py               #   Configuración de la app
│   ├── adapters/            #   Adaptadores hexagonales (vacíos)
│   └── migrations/          #   Historial de cambios en la DB
│
├── templates/               #  Plantillas HTML
│   ├── base.html            #   Plantilla base (header, nav, footer)
│   ├── inicio.html          #   Landing page (página de bienvenida)
│   ├── login.html           #   Inicio de sesión
│   ├── registro.html        #   Registro de nuevo cliente
│   ├── dashboard.html       #   Panel principal del cliente
│   ├── transferencia.html   #   Formulario de transferencia
│   └── transferencia_exito.html  #  Confirmación de transferencia
│
├── static/
│   └── css/
│       └── estilo.css       #  Estilos CSS del sitio
│
├── pruebas/                 #  Tests (vacío por ahora)
│   ├── unitarias/
│   ├── integracion/
│   └── concurrencia/
│
├── .env                     #  Configuración secreta
│                            #   (clave de Django, datos de DB)
├── manage.py                #  Herramienta para comandos de Django
├── requirements.txt         #  Lista de dependencias Python
└── DOCUMENTACION.md         #  Este documento
```

### 📌 Concepto clave: ¿Qué es una app en Django?

Django organiza el código en "apps". Cada app es un módulo que hace una cosa específica. En este proyecto:

- `infrastructure/` es nuestra única app. Contiene los modelos, las vistas, los formularios.
- `config/` es la configuración global del proyecto (no es una app).

---

## 3. El ciclo de vida de una solicitud (Request)

Cuando un usuario escribe una URL en el navegador, pasan varias cosas antes de que vea la página. Veamos el ejemplo de cuando alguien entra a `/login/`:

```
 PASO 1                          PASO 2                          PASO 3
┌──────────────┐           ┌──────────────┐           ┌──────────────────┐
│ Usuario      │  escribe  │  Django      │  busca en  │  config/urls.py  │
│ escribe      │ ────────> │  recibe el   │ ────────> │                  │
│ /login/      │           │  pedido      │           │  'login/' →      │
│              │           │              │           │  LoginView       │
└──────────────┘           └──────────────┘           └────────┬─────────┘
                                                               │
                                                               ▼
 PASO 4                          PASO 5                          PASO 6
┌──────────────────────┐    ┌───────────────┐            ┌───────────────┐
│ LoginView            │    │  LoginView     │            │  Django       │
│ (en auth_views.py)   │    │  obtiene       │            │  completa     │
│                      │    │  datos         │            │  el template  │
│ Ejecuta el código    │ ──>│  y elige       │ ─────────> │  con los      │
│ de la vista          │    │  el template   │            │  datos        │
│                      │    │  login.html    │            │               │
└──────────────────────┘    └───────────────┘            └───────┬───────┘
                                                                  │
                                                                  ▼
 PASO 7                          PASO 8
┌───────────────┐            ┌──────────────────┐
│ Django        │            │ El navegador     │
│ devuelve      │  HTML+CSS  │ pinta la página  │
│ la respuesta  │ ─────────> │ y el usuario     │
│ al navegador  │            │ ve el formulario │
└───────────────┘            └──────────────────┘
```

### Explicación paso a paso

1. **El navegador** hace un pedido (request) a `http://localhost:8000/login/`
2. **Django** recibe el pedido y busca qué hacer con esa URL
3. **`urls.py`** es como una guía telefónica: dice "cuando alguien entre a `login/`, ejecutá la vista `LoginView`"
4. **La vista `LoginView`** se ejecuta. Si es un GET (entrar a la página), muestra el formulario vacío. Si es un POST (enviar el formulario), valida los datos.
5. **La vista** prepara los datos y elige qué template HTML usar
6. **Django** combina el template HTML (login.html) con los datos (el formulario, errores, etc.)
7. **Django devuelve** una página HTML completa al navegador
8. **El navegador** pinta la página y el usuario ve el resultado

> 💡 **Resumen:** URL → urls.py → Vista → Template → HTML → Navegador

---

## 4. Las URLs del sistema

Archivo: `config/urls.py`

```python
from django.urls import path
from django.contrib.auth.views import LogoutView
from infrastructure.auth_views import InicioView, RegistroView, LoginView, DashboardView, TransferenciaView

urlpatterns = [
    path('', InicioView.as_view(), name='inicio'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='inicio'), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('transferencia/', TransferenciaView.as_view(), name='transferencia'),
]
```

**Explicación:**
- Cada `path()` conecta una **URL** con una **vista**
- `name='inicio'` es un nombre que usamos después en los templates con `{% url 'inicio' %}`
- `.as_view()` convierte la clase en una vista usable
- `LogoutView.as_view(next_page='inicio')`: cuando alguien cierra sesión, lo redirige a la página de inicio

### Tabla de rutas

| Ruta | Vista | Template | ¿Requiere login? | ¿Qué hace? |
|---|---|---|---|---|
| `/` | `InicioView` | `inicio.html` | No | Landing page. Si ya estás logueado, redirige al dashboard |
| `/registro/` | `RegistroView` | `registro.html` | No | Muestra formulario de alta. Al enviar, crea usuario y redirige al dashboard |
| `/login/` | `LoginView` | `login.html` | No | Muestra formulario de login. Al enviar, inicia sesión y redirige al dashboard |
| `/logout/` | `LogoutView` | — | Sí | Cierra la sesión y redirige al inicio |
| `/dashboard/` | `DashboardView` | `dashboard.html` | **Sí** | Muestra saldos, cuentas y movimientos |
| `/transferencia/` | `TransferenciaView` | `transferencia.html` | **Sí** | Muestra formulario de transferencia. Al enviar, muestra pantalla de éxito |

> 💡 **Concepto clave:** Las rutas marcadas con **"Sí"** en "¿Requiere login?" usan `LoginRequiredMixin`. Si un usuario no logueado intenta entrar, Django lo redirige automáticamente a `/login/`.

---

## 5. Las Vistas (Class-Based Views)

### ¿Qué es una vista?

En Django, una **vista** es código que recibe un pedido HTTP y devuelve una respuesta (generalmente una página HTML). Las vistas son el "cerebro" del sistema: deciden qué datos mostrar, qué hacer con un formulario, etc.

### ¿Por qué usamos Class-Based Views (CBV)?

En lugar de escribir funciones sueltas, agrupamos la lógica en **clases**. Ventajas:
- **Reutilización:** podemos heredar métodos de Django en lugar de escribirlos
- **Organización:** cada vista tiene métodos específicos (`get()`, `post()`, `get_context_data()`)
- **Menos código:** Django ya trae la mayoría de la funcionalidad lista

---

### InicioView

```python
class InicioView(TemplateView):
    template_name = 'inicio.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
```

**¿Qué hace?**
- `TemplateView` es la vista más simple de Django: solo muestra un template HTML
- `template_name = 'inicio.html'` le dice a Django qué archivo HTML usar
- `dispatch()` se ejecuta **siempre**, antes que cualquier otro método:
  - Si el usuario **ya está logueado** (`request.user.is_authenticated`), lo redirige al dashboard
  - Si **no está logueado**, muestra la landing page normalmente

**Ejemplo concreto:** Si un usuario logueado escribe `/` en el navegador, automáticamente va a parar a `/dashboard/`.

---

### RegistroView

```python
class RegistroView(CreateView):
    form_class = RegistroClienteForm
    template_name = 'registro.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
        login(self.request, user)
        messages.success(self.request, f'¡Bienvenido {user.first_name}! Tu cuenta fue creada con éxito.')
        return redirect(self.get_success_url())
```

**¿Qué hace?**
- `CreateView` es una vista genérica de Django para crear objetos (en este caso, un usuario)
- `form_class` indica qué formulario usar (`RegistroClienteForm`)
- `success_url` es a dónde redirigir después de crear el usuario exitosamente

**Método `form_valid()`** — se ejecuta SOLO si el formulario es válido:
1. `transaction.atomic()`: todo lo que pasa adentro se ejecuta en una transacción. Si algo falla, se deshace todo (como si nunca hubiera pasado). Esencial en un banco.
2. `form.save()`: guarda el usuario en la base de datos
3. `login(self.request, user)`: inicia sesión automáticamente (el usuario no tiene que loguearse después de registrarse)
4. `messages.success()`: muestra un mensaje verde de bienvenida
5. `redirect()`: redirige al dashboard

---

### LoginView

```python
class LoginView(BaseLoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, f'¡Bienvenido de nuevo, {form.get_user().first_name}!')
        return super().form_valid(form)
```

**¿Qué hace?**
- Hereda de `BaseLoginView` (el LoginView que viene con Django)
- Django ya sabe cómo validar usuario/contraseña, iniciar sesión, manejar errores, etc.
- Solo personalizamos:
  - `template_name`: el HTML que usa
  - `form_valid()`: agregamos un mensaje de bienvenida antes de redirigir

**Lo que NO tenemos que escribir (Django lo hace solo):**
- Validar que el usuario existe
- Verificar que la contraseña es correcta
- Crear la sesión
- Redirigir al dashboard

---

### DashboardView

```python
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ... datos mock ...
        context['cliente'] = mock_cliente
        context['cuentas'] = mock_cuentas
        context['transacciones'] = mock_transacciones
        return context
```

**¿Qué hace?**
- `LoginRequiredMixin`: si el usuario no está logueado, lo redirige al login automáticamente
- `get_context_data()`: prepara los datos que se van a mostrar en el template

**¿Qué son los datos mock?** Son datos inventados (ver sección 11). Cuando el sistema sea funcional, `mock_cuentas` se reemplazará por consultas reales a la base de datos.

---

### TransferenciaView

```python
class TransferenciaView(LoginRequiredMixin, TemplateView):
    template_name = 'transferencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuentas'] = [
            {'id': 1, 'tipo': 'Caja de Ahorro', 'numero': '**** 4521', 'saldo': 125430.50, 'moneda': 'ARS'},
            {'id': 2, 'tipo': 'Cuenta Corriente', 'numero': '**** 7890', 'saldo': 8750.00, 'moneda': 'USD'},
        ]
        return context

    def post(self, request, *args, **kwargs):
        # Procesa el formulario cuando se envía
        datos = {
            'origen': ...,
            'destino': request.POST.get('cuenta_destino', ''),
            'monto': request.POST.get('monto', '0.00'),
            'concepto': request.POST.get('concepto', ''),
        }
        return render(request, 'transferencia_exito.html', {'datos': datos})
```

**¿Qué hace?**
- **GET** (entrar a la página): muestra el formulario de transferencia
- **POST** (enviar el formulario): procesa los datos y muestra la pantalla de éxito

`request.POST.get('campo')` obtiene el valor que el usuario escribió en el campo del formulario.

---

## 6. Las Plantillas (Templates)

### ¿Qué es un template?

En Django, los templates son archivos HTML con marcadores especiales que Django completa con datos. Esto permite separar el **diseño** (HTML/CSS) de la **lógica** (Python).

### Herencia de plantillas

Tenemos un archivo `base.html` que contiene la estructura común de todas las páginas:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Banco Hexagonal{% endblock %}</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/estilo.css' %}">
</head>
<body>
  <header class="header">
    <a href="{% url 'inicio' %}" class="logo">Banco Hexagonal</a>
    <nav class="nav">
      <a href="{% url 'inicio' %}">Inicio</a>
      {% if user.is_authenticated %}
        <span class="nav-user">{{ user.username }}</span>
        <a href="{% url 'logout' %}">Cerrar sesión</a>
      {% else %}
        <a href="{% url 'login' %}">Iniciar sesión</a>
        <a href="{% url 'registro' %}">Abrir cuenta</a>
      {% endif %}
    </nav>
  </header>

  <main class="main">
    {% if messages %}
      <div class="messages">
        {% for message in messages %}
          <div class="alert alert-{{ message.tags }}">{{ message }}</div>
        {% endfor %}
      </div>
    {% endif %}
    {% block content %}{% endblock %}
  </main>

  <footer class="footer">
    <p>&copy; {% now "Y" %} Banco Hexagonal.</p>
  </footer>
</body>
</html>
```

**Explicación de cada parte:**

| Marcador | ¿Qué hace? |
|---|---|
| `{% block title %}` | Define una zona que las páginas hijas pueden llenar con su propio título |
| `{% load static %}` | Carga los archivos estáticos (CSS, imágenes) |
| `{% static 'css/estilo.css' %}` | Genera la URL correcta hacia el archivo CSS |
| `{% url 'login' %}` | Genera la URL de la ruta llamada 'login' |
| `{% if user.is_authenticated %}` | Muestra cosas diferentes si el usuario está o no logueado |
| `{{ user.username }}` | Muestra el nombre de usuario |
| `{% if messages %}` | Muestra mensajes flash (si hay) |
| `{% block content %}` | Zona donde cada página pone su contenido específico |
| `{% now "Y" %}` | Muestra el año actual (para el copyright) |

### Cómo funciona la herencia

Cada página del sistema hace:

```html
{% extends 'base.html' %}
{% block title %}Título de esta página{% endblock %}
{% block content %}
  <!-- Contenido específico de esta página -->
{% endblock %}
```

Es como si `base.html` fuera un **molde** y cada página solo completa los huecos (`title` y `content`). Esto evita repetir el header, el nav y el footer en cada archivo.

### Variables en templates

Las vistas pasan datos a los templates a través de un diccionario. Por ejemplo, en `DashboardView`:

```python
context = {
    'cliente': {'nombre': 'Juan', 'email': 'juan@mail.com'},
    'cuentas': [...],
    'transacciones': [...],
}
return render(request, 'dashboard.html', context)
```

Y en el template accedemos a esos datos:

```html
<h2>Hola, {{ cliente.nombre }}!</h2>     <!-- Muestra: Hola, Juan! -->
<p>Email: {{ cliente.email }}</p>         <!-- Muestra: Email: juan@mail.com -->
```

### Filtros de template

Los filtros transforman los datos antes de mostrarlos:

```html
{{ c.saldo|floatformat:2 }}           <!-- 125430.5 → 125430.50 -->
{{ c.saldo|floatformat:2|intcomma }}  <!-- 125430.50 → 125,430.50 -->
{{ t.monto|default:"0.00" }}          <!-- Si está vacío, muestra 0.00 -->
{{ c.estado|title }}                  <!-- "activa" → "Activa" -->
```

> 💡 `|intcomma` viene de `django.contrib.humanize`. Hay que cargarlo con `{% load humanize %}` al inicio del template.

### El formulario en templates (CSRF)

```html
<form method="post" novalidate>
  {% csrf_token %}
  <input type="text" name="username" ...>
  <button type="submit">Ingresar</button>
</form>
```

`{% csrf_token %}` genera un token de seguridad único. Sin esto, Django rechazaría el formulario (es una protección contra ataques CSRF).

---

## 7. Los Modelos (Base de datos)

### ¿Qué es un modelo?

En Django, un **modelo** es una clase Python que representa una tabla en la base de datos. Cada **atributo** de la clase es una **columna** de la tabla. Cada **objeto** (instancia) es una **fila**.

### Diagrama de relaciones

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│     User     │  1:1  │   Cliente    │  1:N  │    Cuenta    │  1:N  │  Transaccion │
│  (Django)    │──────>│              │──────>│              │──────>│              │
├──────────────┤       ├──────────────┤       ├──────────────┤       ├──────────────┤
│ username     │       │ teléfono     │       │ tipo         │       │ tipo         │
│ password     │       │ dirección    │       │ saldo        │       │ monto        │
│ email        │       │ estado       │       │ moneda       │       │ origen       │
│ first_name   │       │ fecha_reg    │       │ límite_diario│       │ destino      │
│ last_name    │       └──────────────┘       └──────────────┘       │ fecha        │
└──────────────┘                                                    │ estado       │
                                                                    │ riesgo       │
                                                                    └──────────────┘
```

- **1:1** (OneToOne): un User tiene exactamente un Cliente, y viceversa
- **1:N** (ForeignKey): un Cliente puede tener varias Cuentas
- **1:N**: una Cuenta puede tener varias Transacciones

---

### Modelo Cliente

```python
class Cliente(models.Model):
    GENERO = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('N', 'No especifica'),
    ]

    NIVEL_EDUCATIVO = [
        ('primario', 'Primario'),
        ('secundario', 'Secundario'),
        ('terciario', 'Terciario/Tecnicatura'),
        ('universitario', 'Universitario'),
        ('posgrado', 'Posgrado/Master'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    dni = models.CharField(max_length=8, unique=True, default='', help_text="Documento Nacional de Identidad único")

    telefono = models.CharField(max_length=20, blank=True, default='')
    direccion = models.TextField(blank=True, default='')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='activo')

    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO, default='N')
    profesion = models.CharField(max_length=100, blank=True, verbose_name="Ocupación/Profesión")
    ingreso_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    nivel_educativo = models.CharField(max_length=20, choices=NIVEL_EDUCATIVO, default='secundario')
    score_crediticio_inicial = models.IntegerField(default=500, help_text="Score externo de riesgo al registrarse")

    class Meta:
        ordering = ['-fecha_registro']

    @property
    def nombre(self):
        return self.usuario.first_name or self.usuario.username

    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name} (DNI: {self.dni})"
```

**Campo por campo (nuevos respecto a la versión original):**

| Campo | Tipo | ¿Qué guarda? |
|---|---|---|
| `dni` | CharField(8, unique) | Documento Nacional de Identidad. Es único y obligatorio. |
| `fecha_nacimiento` | DateField(null) | Fecha de nacimiento (opcional, para minería de datos) |
| `genero` | CharField(choices) | M, F o N (No especifica). Para segmentación. |
| `profesion` | CharField(100) | Ocupación del cliente (opcional) |
| `ingreso_mensual` | DecimalField(12,2) | Ingreso mensual estimado (para score crediticio) |
| `nivel_educativo` | CharField(choices) | primario, secundario, terciario, universitario o posgrado |
| `score_crediticio_inicial` | IntegerField | Puntaje de riesgo asignado externamente al registrar |

> 💡 `blank=True, default=''` en teléfono y dirección significa que el campo no es obligatorio. Esto es importante porque el `Cliente` se crea automáticamente con una **señal** (ver sección 9) y en ese momento no tenemos esos datos todavía.

**`class Meta: ordering`:** cuando consultamos clientes, por defecto vienen ordenados del más reciente al más antiguo (`-fecha_registro` = orden descendente).

**`@property nombre`:** permite acceder al nombre del cliente como `cliente.nombre` (devuelve `first_name` y si está vacío, el `username`). Útil tanto para templates como para datos mock.

**`__str__`:** define cómo se muestra un Cliente cuando lo imprimimos. Por ejemplo, `print(cliente)` muestra "Juan Pérez (DNI: 12345678)".

---

### Modelo Cuenta

```python
class Cuenta(models.Model):
    TIPO_CUENTA = [('ahorro', 'Ahorro'), ('corriente', 'Corriente')]
    ESTADO_CUENTA = [('activa', 'Activa'), ('inactiva', 'Inactiva'), ('bloqueada', 'Bloqueada')]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cuentas')
    tipo_cuenta = models.CharField(max_length=20, choices=TIPO_CUENTA)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    moneda = models.CharField(max_length=3, default='USD')
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CUENTA, default='activa')
    limite_transferencia_diario = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)

    class Meta:
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f"Cuenta {self.id} - {self.cliente.usuario.username}"
```

**Campo por campo:**

| Campo | Tipo | ¿Qué guarda? |
|---|---|---|
| `cliente` | ForeignKey(Cliente) | ¿De quién es esta cuenta? `related_name='cuentas'` permite hacer `cliente.cuentas.all()` |
| `tipo_cuenta` | CharField(choices) | "ahorro" o "corriente" |
| `saldo` | DecimalField(12,2) | Dinero disponible. 12 dígitos, 2 decimales. |
| `moneda` | CharField(3) | ARS (pesos) o USD (dólares) |
| `estado` | CharField(choices) | "activa", "inactiva" o "bloqueada" |
| `limite_transferencia_diario` | DecimalField(12,2) | Máximo que se puede transferir por día |

> 💡 `on_delete=models.PROTECT`: si alguien intenta borrar un Cliente que tiene cuentas, Django lo impide. No se puede borrar un cliente si tiene cuentas activas. Esto es importante en un banco.

---

### Modelo Transaccion

```python
class Transaccion(models.Model):
    TIPO_TRANSACCION = [
        ('transferencia', 'Transferencia'),
        ('deposito', 'Depósito'),
        ('retiro', 'Retiro'),
    ]
    ESTADO_TRANSACCION = [
        ('completada', 'Completada'),
        ('pendiente', 'Pendiente'),
        ('fallida', 'Fallida'),
        ('revertida', 'Revertida'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_TRANSACCION, db_index=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    cuenta_origen = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='transacciones_origen', null=True, blank=True)
    cuenta_destino = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='transacciones_destino', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    estado = models.CharField(max_length=20, choices=ESTADO_TRANSACCION, default='completada', db_index=True)
    descripcion = models.TextField(blank=True)
    riesgo_fraude = models.FloatField(default=0.0)
    es_fraude_confirmado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Transacción {self.id} - {self.tipo} - {self.monto}"
```

**Campo por campo:**

| Campo | Tipo | ¿Qué guarda? |
|---|---|---|
| `tipo` | CharField(choices) | transferencia, depósito o retiro |
| `monto` | DecimalField(12,2) | Cantidad de dinero transferida |
| `cuenta_origen` | ForeignKey(Cuenta) | De qué cuenta salió el dinero (puede ser nulo: ej. depósito en efectivo) |
| `cuenta_destino` | ForeignKey(Cuenta) | A qué cuenta entró el dinero (puede ser nulo: ej. retiro) |
| `fecha_creacion` | DateTimeField(auto_now_add) | Cuándo se hizo la transacción |
| `estado` | CharField(choices) | completada, pendiente, fallida, revertida |
| `riesgo_fraude` | FloatField | Puntaje de 0 a 1: ¿qué tan probable es que sea fraude? (para ML) |
| `es_fraude_confirmado` | BooleanField | True si se confirmó que es fraude |

> 💡 `db_index=True` en `tipo`, `fecha_creacion` y `estado`: estos campos se usan mucho en búsquedas. El índice hace que las consultas sean más rápidas (como el índice de un libro).

---

### Modelo ConfiguracionSeguridad

```python
class ConfiguracionSeguridad(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='configuracion_seguridad')
    intentos_fallidos_login = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    doble_factor_activo = models.BooleanField(default=False)
```

**¿Para qué sirve?**
Controla la seguridad de cada cliente: cuántos intentos de login fallidos tuvo, si está bloqueado temporalmente y si tiene doble factor activado. Relación 1:1 con Cliente (cada cliente tiene exactamente una configuración).

---

### Modelo Tarjeta

```python
class Tarjeta(models.Model):
    TIPO_TARJETA = [('debito', 'Débito'), ('credito', 'Crédito')]
    ESTADO_TARJETA = [('activa', 'Activa'), ('bloqueada', 'Bloqueada'), ('vencida', 'Vencida')]

    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='tarjetas')
    tipo_tarjeta = models.CharField(max_length=20, choices=TIPO_TARJETA)
    numero = models.CharField(max_length=16, unique=True)
    cvv = models.CharField(max_length=4)
    fecha_expiracion = models.DateField()
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, choices=ESTADO_TARJETA, default='activa')
```

| Campo | Tipo | ¿Qué guarda? |
|---|---|---|
| `cuenta` | ForeignKey(Cuenta) | A qué cuenta está asociada la tarjeta |
| `numero` | CharField(16, unique) | Número de tarjeta de 16 dígitos |
| `cvv` | CharField(4) | Código de seguridad trasero |
| `limite_credito` | DecimalField(12,2) | Límite de crédito (solo para tarjetas de crédito) |
| `saldo_actual` | DecimalField(12,2) | Saldo disponible o deuda actual |

---

### Modelo Prestamo

```python
class Prestamo(models.Model):
    ESTADO_PRESTAMO = [('activo', 'Activo'), ('pagado', 'Pagado'), ('vencido', 'Vencida/Mora')]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='prestamos')
    monto_original = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_interes_anual = models.FloatField()
    plazo_meses = models.IntegerField()
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PRESTAMO, default='activo')
```

Los préstamos se pagan en **cuotas**. Cada préstamo tiene varias cuotas, representadas en el modelo `CuotaPrestamo`:

```python
class CuotaPrestamo(models.Model):
    ESTADO_CUOTA = [('pendiente', 'Pendiente'), ('pagada', 'Pagada'), ('vencida', 'Vencida')]

    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='cuotas')
    numero_cuota = models.IntegerField()
    monto_cuota = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CUOTA, default='pendiente')
```

Relación: un **Préstamo** tiene muchas **Cuotas**. Cada cuota tiene su propio vencimiento y estado. `on_delete=models.PROTECT` en Prestamo.cliente evita borrar clientes con préstamos activos.

---

### Modelo AlertaFraude

```python
class AlertaFraude(models.Model):
    ACCIONES_SISTEMA = [
        ('ninguna', 'Ninguna / En revisión'),
        ('bloqueo_cuenta', 'Bloqueo de Cuenta'),
        ('notificacion_cliente', 'Notificación Enviada'),
        ('transaccion_rechazada', 'Transacción Rechazada'),
    ]

    transaccion = models.OneToOneField(Transaccion, on_delete=models.CASCADE, related_name='alerta')
    score_riesgo = models.FloatField()
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    accion_tomada = models.CharField(max_length=50, choices=ACCIONES_SISTEMA, default='ninguna')
    resuelta = models.BooleanField(default=False)
```

**¿Para qué sirve?**
Cuando el motor de Machine Learning detecta una transacción sospechosa, crea una alerta con un score de riesgo. El sistema puede tomar acciones automáticas (bloquear cuenta, rechazar transacción) y el cliente puede revisarlas después. Relación 1:1 con Transaccion.

---

### Diagrama completo de relaciones

```
┌──────────────────┐       ┌───────────────────┐       ┌───────────────┐       ┌──────────────────┐
│      User        │  1:1  │     Cliente       │  1:N  │    Cuenta     │  1:N  │   Transaccion    │
│   (Django)       │──────>│                   │──────>│               │──────>│                  │
├──────────────────┤       ├───────────────────┤       ├───────────────┤       ├──────────────────┤
│ username         │       │ dni (unique)      │       │ tipo_cuenta   │       │ tipo (db_index)  │
│ password (hash)  │       │ telefono          │       │ saldo         │       │ monto            │
│ email            │       │ direccion         │       │ moneda        │       │ cuenta_origen    │
│ first_name       │       │ fecha_registro    │       │ estado        │       │ cuenta_destino   │
│ last_name        │       │ estado            │       │ limite_diario │       │ fecha_creacion   │
└──────────────────┘       │ fecha_nacimiento  │       └───────┬───────┘       │ estado (db_index)│
                           │ genero            │               │              │ riesgo_fraude    │
                           │ profesion         │               │ 1:N          │ es_fraude        │
                           │ ingreso_mensual   │               │              └────────┬─────────┘
                           │ nivel_educativo   │               ▼                       │
                           │ score_crediticio  │       ┌───────────────┐              │
                           └────────┬──────────┘       │   Tarjeta    │              │ 1:1
                                    │                  ├───────────────┤              ▼
                                    │ 1:1              │ tipo (débito/ │       ┌───────────────┐
                                    ▼                  │  crédito)     │       │ AlertaFraude  │
                           ┌───────────────────┐       │ numero (16d)  │       ├───────────────┤
                           │ ConfiguracionSeg  │       │ cvv           │       │ score_riesgo  │
                           ├───────────────────┤       │ fecha_exp     │       │ accion_tomada │
                           │ intentos_fallidos │       │ limite_cred   │       │ resuelta      │
                           │ bloqueado_hasta   │       │ saldo_actual  │       └───────────────┘
                           │ doble_factor      │       └───────────────┘
                           └───────────────────┘

  ┌──────────────────┐
  │    Prestamo      │  1:N  ┌──────────────┐
  ├──────────────────┤──────>│ CuotaPrestamo│
  │ monto_original   │       ├──────────────┤
  │ saldo_pendiente  │       │ numero_cuota │
  │ tasa_interes     │       │ monto_cuota  │
  │ plazo_meses      │       │ fecha_vencim │
  │ estado           │       │ estado       │
  └──────────────────┘       └──────────────┘
```

### Cómo se relacionan los modelos

```python
# Un cliente y sus cuentas
cliente = Cliente.objects.get(id=1)
cuentas = cliente.cuentas.all()           # gracias a related_name='cuentas'
config = cliente.configuracion_seguridad   # 1:1, related_name='configuracion_seguridad'
prestamos = cliente.prestamos.all()        # gracias a related_name='prestamos'

# Una cuenta y sus tarjetas
cuenta = Cuenta.objects.get(id=1)
tarjetas = cuenta.tarjetas.all()           # gracias a related_name='tarjetas'

# Una cuenta y sus transacciones
transacciones_salida = cuenta.transacciones_origen.all()    # lo que salió
transacciones_entrada = cuenta.transacciones_destino.all()  # lo que entró

# Una transacción y su alerta de fraude
transaccion = Transaccion.objects.get(id=1)
alerta = transaccion.alerta                # 1:1, puede ser None si no hay alerta

# Un préstamo y sus cuotas
prestamo = Prestamo.objects.get(id=1)
cuotas = prestamo.cuotas.all()             # gracias a related_name='cuotas'
```

---

## 8. El Formulario de Registro

Archivo: `infrastructure/forms.py`

```python
class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')

    telefono = forms.CharField(max_length=20, required=True, label='Teléfono')
    direccion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True, label='Dirección')

    dni = forms.CharField(max_length=8, required=True, label='DNI',
                           help_text='Documento Nacional de Identidad (8 dígitos)')
    fecha_nacimiento = forms.DateField(
        required=False, label='Fecha de nacimiento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    genero = forms.ChoiceField(choices=Cliente.GENERO, required=False, label='Género')
    profesion = forms.CharField(max_length=100, required=False, label='Ocupación/Profesión')
    ingreso_mensual = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False, label='Ingreso mensual')
    nivel_educativo = forms.ChoiceField(
        choices=Cliente.NIVEL_EDUCATIVO, required=False, label='Nivel educativo')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            cliente = user.cliente
            cliente.telefono = self.cleaned_data['telefono']
            cliente.direccion = self.cleaned_data['direccion']
            cliente.dni = self.cleaned_data['dni']
            if self.cleaned_data.get('fecha_nacimiento'):
                cliente.fecha_nacimiento = self.cleaned_data['fecha_nacimiento']
            if self.cleaned_data.get('genero'):
                cliente.genero = self.cleaned_data['genero']
            if self.cleaned_data.get('profesion'):
                cliente.profesion = self.cleaned_data['profesion']
            if self.cleaned_data.get('ingreso_mensual') is not None:
                cliente.ingreso_mensual = self.cleaned_data['ingreso_mensual']
            if self.cleaned_data.get('nivel_educativo'):
                cliente.nivel_educativo = self.cleaned_data['nivel_educativo']
            cliente.save()
        return user
```

### ¿De dónde viene `UserCreationForm`?

Es un formulario que **ya viene con Django**. Hace automáticamente:

1. Pide usuario, contraseña y confirmación de contraseña
2. Valida que la contraseña sea segura (mínimo 8 caracteres, no sea común, etc.)
3. Hashea la contraseña con **PBKDF2** (no guarda la contraseña en texto plano)
4. Crea el usuario en la base de datos

Nosotros **extendemos** este formulario agregando muchos campos extra que se guardan en el User (nombre, apellido, email) y en el Cliente (teléfono, dirección, DNI, fecha de nacimiento, género, profesión, ingreso mensual, nivel educativo).

### Campos nuevos del registro (vs. versión original)

| Campo | ¿Requerido? | ¿Dónde se guarda? |
|---|---|---|
| `dni` | Sí (único) | Cliente.dni |
| `fecha_nacimiento` | No | Cliente.fecha_nacimiento |
| `genero` | No | Cliente.genero (M/F/N) |
| `profesion` | No | Cliente.profesion |
| `ingreso_mensual` | No | Cliente.ingreso_mensual |
| `nivel_educativo` | No | Cliente.nivel_educativo |

### Método `save()` explicado

```python
def save(self, commit=True):
    user = super().save(commit=False)          # 1. Crea el usuario EN MEMORIA
    user.email = self.cleaned_data['email']         # 2. Agrega campos extra al User
    user.first_name = self.cleaned_data['first_name']
    user.last_name = self.cleaned_data['last_name']
    if commit:
        user.save()                                # 3. Guarda el User en DB
        cliente = user.cliente                     # 4. Obtiene Cliente (creado por señal)
        cliente.telefono = self.cleaned_data['telefono']     # 5. Campos básicos
        cliente.direccion = self.cleaned_data['direccion']
        cliente.dni = self.cleaned_data['dni']               # 6. Campos de minería de datos
        if self.cleaned_data.get('fecha_nacimiento'):
            cliente.fecha_nacimiento = self.cleaned_data['fecha_nacimiento']
        if self.cleaned_data.get('genero'):
            cliente.genero = self.cleaned_data['genero']
        if self.cleaned_data.get('profesion'):
            cliente.profesion = self.cleaned_data['profesion']
        if self.cleaned_data.get('ingreso_mensual') is not None:
            cliente.ingreso_mensual = self.cleaned_data['ingreso_mensual']
        if self.cleaned_data.get('nivel_educativo'):
            cliente.nivel_educativo = self.cleaned_data['nivel_educativo']
        cliente.save()                             # 7. Guarda todo
    return user
```

**¿Por qué `user.cliente` ya existe?** Porque cuando se ejecuta `user.save()` en el paso 3, la **señal** `post_save` (explicada en la sección 9) crea automáticamente un `Cliente` vacío para ese usuario. Después solo completamos los datos que faltan.

**¿Por qué algunos campos usan `self.cleaned_data.get()` en vez de `self.cleaned_data[]`?** Porque son opcionales. Si el usuario no los completa, no envía el campo en el formulario. `.get()` devuelve `None` si no existe, y el `if` evita pisar el default del modelo con `None`.

---

## 9. Las Señales (Signals)

### ¿Qué es una señal?

Una señal es código que se ejecuta **automáticamente** cuando ocurre un evento en otra parte del sistema. Es como un "aviso": "cuando pase X, ejecutá Y".

### La señal que usamos

Archivo: `infrastructure/signals.py`

```python
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Cliente

@receiver(post_save, sender=User)
def crear_cliente(sender, instance, created, **kwargs):
    if created:
        Cliente.objects.create(usuario=instance)
```

**¿Qué significa cada parte?**

| Parte | Significado |
|---|---|
| `@receiver` | Decorador que registra esta función como una señal |
| `post_save` | Evento: "después de guardar" algo |
| `sender=User` | ¿Qué cosa se guardó? Un User |
| `instance` | El User que se acaba de guardar |
| `created` | True si es NUEVO, False si solo se actualizó |
| `Cliente.objects.create(usuario=instance)` | Crea un Cliente vinculado a ese User |

**Flujo completo:**

```
1. Alguien crea un User (desde el registro, desde el admin, desde la terminal)
2. Django guarda el User en la base de datos
3. Inmediatamente después, Django ejecuta la señal
4. La señal crea un Cliente con ese usuario (teléfono y dirección vacíos)
5. Si el User se creó desde el formulario de registro, después el formulario completa teléfono y dirección
```

### ¿Por qué es mejor que crear el Cliente en el formulario?

**Sin señal:** Si creaban un usuario desde el admin de Django, NO se creaba el Cliente. El sistema quedaba inconsistente (un usuario sin perfil de cliente).

**Con señal:** No importa desde dónde se cree el usuario — el Cliente se crea automáticamente siempre.

### ¿Cómo se activa la señal?

En `infrastructure/apps.py`:

```python
class InfrastructureConfig(AppConfig):
    name = 'infrastructure'

    def ready(self):
        import infrastructure.signals  # ← aquí se registra la señal
```

Django ejecuta `ready()` cuando arranca, y eso importa el archivo `signals.py`, lo que registra la función `crear_cliente` como una señal.

---

## 10. Mensajes Flash

### ¿Qué son?

Son mensajes que aparecen una sola vez y **desaparecen al recargar la página**. Se usan para notificaciones: "Bienvenido", "Cuenta creada con éxito", etc.

### Cómo se crean (en las vistas)

```python
from django.contrib import messages

messages.success(request, '¡Bienvenido!')    # Mensaje verde (éxito)
messages.error(request, 'Algo salió mal')    # Mensaje rojo (error)
messages.info(request, 'Recordatorio...')    # Mensaje azul (informativo)
messages.warning(request, 'Cuidado...')      # Mensaje amarillo (advertencia)
```

### Dónde se usan en el proyecto

En `auth_views.py`:

```python
# Después de registrarse
messages.success(self.request, f'¡Bienvenido {user.first_name}! Tu cuenta fue creada con éxito.')

# Después de iniciar sesión
messages.success(self.request, f'¡Bienvenido de nuevo, {form.get_user().first_name}!')
```

### Cómo se muestran (en los templates)

En `base.html`:

```html
{% if messages %}
  <div class="messages">
    {% for message in messages %}
      <div class="alert alert-{{ message.tags }}">{{ message }}</div>
    {% endfor %}
  </div>
{% endif %}
```

- `message.tags` contiene la clase CSS correspondiente: `success`, `error`, `info`, `warning`
- El CSS les da color: verde para éxito, rojo para error, etc.

---

## 11. Datos Mock (de mentira)

### ¿Qué son y por qué existen?

Como todavía no hemos implementado la lógica bancaria real (crear cuentas, hacer transferencias de verdad), usamos **datos inventados** para que el sistema se vea funcionando.

Están definidos en `DashboardView.get_context_data()` y `TransferenciaView.get_context_data()`.

### Código actual (mock)

```python
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ── DATOS MOCK ──────────────────────────────
        # TODO: Reemplazar con consultas reales a la DB
        mock_cliente = {
            'nombre': self.request.user.first_name or self.request.user.username,
            'apellido': self.request.user.last_name,
            'email': self.request.user.email,
        }

        mock_cuentas = [
            {'tipo': 'Caja de Ahorro', 'numero': '**** 4521', 'saldo': 125430.50, 'moneda': 'ARS', 'estado': 'activa'},
            {'tipo': 'Cuenta Corriente', 'numero': '**** 7890', 'saldo': 8750.00, 'moneda': 'USD', 'estado': 'activa'},
        ]

        mock_transacciones = [
            {'fecha': '05/06/2026', 'tipo': 'Transferencia', 'descripcion': 'Transferencia a Juan Pérez', 'monto': -15000.00},
            {'fecha': '04/06/2026', 'tipo': 'Depósito', 'descripcion': 'Depósito en efectivo', 'monto': 50000.00},
            # ... más transacciones ...
        ]
        # ── FIN DATOS MOCK ──────────────────────────

        context['cliente'] = mock_cliente
        context['cuentas'] = mock_cuentas
        context['transacciones'] = mock_transacciones
        return context
```

### Cómo se reemplazará después

Cuando implementen la lógica real, esto se cambiará por:

```python
from django.shortcuts import get_object_or_404
from .models import Cliente, Cuenta, Transaccion

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    
    cliente = get_object_or_404(Cliente, usuario=self.request.user)
    cuentas = Cuenta.objects.filter(cliente=cliente)
    transacciones = Transaccion.objects.filter(
        cuenta_origen__in=cuentas
    ) | Transaccion.objects.filter(
        cuenta_destino__in=cuentas
    )
    
    context['cliente'] = cliente               # ← se pasa el modelo directamente
    context['cuentas'] = cuentas
    context['transacciones'] = transacciones.order_by('-fecha_creacion')[:10]
    return context
```

**¿Por qué funciona `{{ cliente.nombre }}` en el template con un modelo real?** Porque agregamos la **propiedad** `nombre` en el modelo `Cliente`:

```python
@property
def nombre(self):
    return self.usuario.first_name or self.usuario.username
```

Esto permite que `cliente.nombre` funcione tanto con el diccionario mock actual como con una instancia real de `Cliente` cuando se migre a datos reales. El template no necesita cambios.

**Diferencia clave:** Hoy los datos están escritos a mano en el código. Cuando sea funcional, los datos vendrán de la base de datos real.

---

## 12. Arquitectura: Híbrido Hexagonal + MTV

### 12.1 ¿Qué es la arquitectura hexagonal?

Imaginá un **enchufe** y un **aparato eléctrico**:

- El enchufe (puerto) tiene una forma estándar
- Cualquier aparato que tenga esa forma (adaptador) puede conectarse
- El aparato no necesita saber si la electricidad viene de una central nuclear, un panel solar o un generador

La arquitectura hexagonal funciona igual:

```
            ┌──────────────────────┐
            │    LÓGICA DE         │
            │    NEGOCIO           │
            │  (Domain/Application)│
            │                      │
            │  No sabe si los      │
            │  datos vienen de     │
            │  PostgreSQL, MySQL   │
            │  o un archivo JSON   │
            └────────┬──┬──────────┘
                     │  │
          ┌──────────┘  └──────────┐
          ▼                        ▼
   ┌──────────────┐         ┌──────────────┐
   │  Adaptador   │         │  Adaptador   │
   │  PostgreSQL  │         │  MongoDB     │
   │              │         │              │
   │  Implementa  │         │  Implementa  │
   │  el puerto   │         │  el puerto   │
   └──────────────┘         └──────────────┘
```

**En nuestro proyecto:**

| Capa | ¿Qué va acá? | ¿Depende de Django? |
|---|---|---|
| **Domain** (dominio) | Entidades de negocio: `CuentaEntity`, `TransaccionEntity` | ❌ No |
| **Domain/ports** | Interfaces: `class RepositorioCuenta(ABC)` | ❌ No |
| **Domain/reglas** | Reglas de negocio: `validar_saldo_suficiente()` | ❌ No |
| **Application** | Casos de uso: `RealizarTransferencia.ejecutar()` | ❌ No |
| **Infrastructure/adapters** | Implementaciones concretas: `RepositorioCuentaORM` | ✅ Sí (usa Django ORM) |
| **Infrastructure/views** | Vistas que conectan el navegador con los casos de uso | ✅ Sí |

**Ventaja:** Si mañana cambiamos de PostgreSQL a MySQL, solo tocamos el adaptador. La lógica de negocio (domain + application) no se modifica. Ni siquiera sabe qué base de datos se usa.

### 12.2 ¿Por qué no hicimos hexagonal puro?

Cuando arrancamos el proyecto, nos dimos cuenta de que Django ya resuelve muchos problemas de forma excelente. Decidimos ser **pragmáticos**: usar Django donde ya es fuerte, y preparar hexagonal donde la lógica de negocio lo requiere.

| Módulo | Arquitectura | ¿Por qué esta decisión? |
|---|---|---|
| **Registro / Login** | MTV clásico de Django | Django tiene años de auditoría de seguridad en autenticación: hasheo de contraseñas con PBKDF2, protección contra timing attacks, CSRF, sesiones seguras. Reescribir todo eso para "ser hexagonal" sería inseguro y una pérdida de tiempo. |
| **Dashboard** | MTV clásico | Es solo mostrar información. No hay lógica de negocio compleja que aislar. |
| **Transferencias** (futuro) | **Hexagonal** | La lógica de transferencias involucra concurrencia (`select_for_update`), reglas de negocio (límite diario, saldo suficiente), y necesita ser testeable sin base de datos. |
| **Detección de fraude** (futuro) | **Hexagonal** | Poder cambiar entre Scikit-learn y PyTorch sin tocar la lógica de negocio. |

### 12.3 ¿Qué ventajas nos da cada cosa de Django?

| Feature de Django | Si lo hiciéramos con un adaptador propio... | Ventaja de usar Django |
|---|---|---|
| **`UserCreationForm`** | Tendríamos que validar contraseñas, hashear con PBKDF2, verificar que no sea una contraseña común, proteger contra timing attacks | Django ya lo hace, auditado por miles de desarrolladores |
| **`LoginView`** | Manejar sesiones, cookies, expiración, redirección post-login | Django gestiona sesiones seguras con cookies firmadas |
| **`@login_required`** | Verificar en cada request si el usuario tiene sesión activa | Una línea de código protege toda una vista |
| **CSRF token** | Generar token único, verificar en cada POST, rotar tokens | Django lo hace automáticamente con `{% csrf_token %}` |
| **ORM** | Escribir SQL a mano, escapando inputs para evitar SQL injection | El ORM genera SQL parametrizado, immune a SQL injection |
| **`messages`** | Guardar notificaciones en sesión, mostrarlas una vez y borrarlas | Django maneja el ciclo de vida completo |
| **`transaction.atomic()`** | Manejar manualmente BEGIN/COMMIT/ROLLBACK | Garantiza atomicidad: si algo falla, todo se revierte |

### 12.4 ¿Dónde va a estar el hexagonal entonces?

En las carpetas `domain/`, `application/` y `infrastructure/adapters/`. Cuando implementemos las transferencias reales, el flujo será:

```
                    ┌───────────────────────────────────────┐
                    │           Vista Django                 │
                    │  TransferenciaView (POST)              │
                    │  Recibe los datos del formulario       │
                    └──────────────┬────────────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────────────┐
                    │        Caso de Uso (Application)       │
                    │  RealizarTransferencia.ejecutar()      │
                    │  Orquesta la operación:                │
                    │   1. Validar reglas de negocio         │
                    │   2. Ejecutar la transferencia         │
                    │   3. Guardar el resultado              │
                    └──────────────┬────────────────────────┘
                                   │
                    ┌──────────────┴────────────────────────┐
                    │                                       │
                    ▼                                       ▼
        ┌──────────────────────┐              ┌──────────────────────┐
        │  Puerto (Interface)  │              │  Puerto (Interface)  │
        │  RepositorioCuenta   │              │ RepositorioTx        │
        └──────────┬───────────┘              └──────────┬───────────┘
                   │                                     │
                   ▼                                     ▼
        ┌──────────────────────┐              ┌──────────────────────┐
        │  Adaptador ORM      │              │  Adaptador ORM       │
        │  (Django models)    │              │  (Django models)     │
        │                      │              │                      │
        │  Cuenta.objects      │              │  Transaccion.objects │
        │  .select_for_update()│              │  .create()           │
        └──────────────────────┘              └──────────────────────┘
                   │                                     │
                   ▼                                     ▼
        ┌──────────────────────────────────────────────────────┐
        │              PostgreSQL (Base de datos)               │
        └──────────────────────────────────────────────────────┘
```

**Beneficio académico de esta arquitectura:**

1. Las **reglas de negocio** (`domain/reglas/`) se prueban sin base de datos — son funciones puras
2. Los **casos de uso** (`application/`) se prueban con mocks — no necesitan Django
3. Los **adaptadores** (`infrastructure/adapters/`) son delgados — solo conectan el ORM con los puertos
4. Si cambiamos de base de datos o de framework web, la lógica de negocio no se toca

---

## 13. Glosario Django

| Término | Significado (simple) |
|---|---|
| **Django** | Framework web de Python que ya trae resuelto lo más común: rutas, base de datos, formularios, seguridad |
| **View** | Función o clase que recibe un pedido del navegador y decide qué responder |
| **CBV (Class-Based View)** | Vista escrita como clase en vez de función. Permite reutilizar métodos y organizar mejor el código |
| **Template** | Archivo HTML con marcadores `{{ }}` y `{% %}` que Django completa con datos |
| **DTL (Django Template Language)** | El lenguaje de los templates: `{{ variable }}`, `{% if %}`, `{% for %}`, `{% url %}` |
| **Block** | Zona de un template que las páginas hijas pueden llenar (`{% block content %}`) |
| **Model** | Clase Python que representa una tabla en la base de datos |
| **Field** | Columna de una tabla (ej: `CharField` = texto, `DecimalField` = número con decimales) |
| **ORM** | Forma de hablar con la base de datos usando objetos Python en vez de escribir SQL |
| **Migration** | Archivo que describe cambios en la estructura de la base de datos (crear tabla, agregar columna) |
| **Form** | Clase que define los campos de un formulario HTML y cómo validarlos |
| **CSRF** | Token de seguridad único que Django agrega a cada formulario. Evita ataques donde un sitio externo envía datos a nuestro sitio sin que el usuario lo sepa |
| **Signal** | Código que se ejecuta automáticamente cuando ocurre un evento (ej: crear Cliente al crear User) |
| **Middleware** | Código que se ejecuta en cada pedido, como un filtro. Ej: verificar sesión, proteger contra ataques |
| **`@login_required`** | Decorador que protege una vista: si el usuario no está logueado, lo redirige al login |
| **`LoginRequiredMixin`** | Lo mismo que `@login_required` pero para Class-Based Views |
| **`select_for_update`** | Bloqueo en la base de datos: cuando una transacción está en curso, otras esperan. Esencial para concurrencia bancaria |
| **`transaction.atomic()`** | Todo lo que pasa adentro se ejecuta como una unidad: si algo falla, se deshace todo |
| **`auto_now_add=True`** | El campo se llena automáticamente con la fecha/hora actual cuando se crea el registro |
| **`on_delete=models.CASCADE`** | Si se borra el objeto vinculado, se borra este también |
| **`on_delete=models.PROTECT`** | Si se intenta borrar el objeto vinculado, Django lo impide (seguridad) |
| **`related_name`** | Nombre para acceder desde el otro lado de la relación. Ej: `cliente.cuentas.all()` |
| **`|floatformat:2`** | Filtro de template: formatea un número con 2 decimales |
| **`|intcomma`** | Filtro de template: agrega separadores de miles. Ej: `125430.50` → `125,430.50` |
| **`python manage.py`** | Herramienta de línea de comandos de Django. Comandos comunes: `runserver` (iniciar el servidor), `check` (verificar errores), `makemigrations` (crear migraciones), `migrate` (aplicar migraciones) |
| **`settings.py`** | Archivo de configuración global: apps instaladas, base de datos, zona horaria, rutas de archivos |

---

*Documentación generada para el proyecto académico Banco Hexagonal.*  
*Última actualización: Junio 2026*
