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
14. [Cómo ejecutar el sistema](#14-cómo-ejecutar-el-sistema)
15. [Concurrencia en Transferencias](#15-concurrencia-en-transferencias)
16. [Machine Learning (Fraude + Scoring)](#16-machine-learning-en-el-sistema)
17. [Plazo Fijo](#17-plazo-fijo)
18. [Historial de Movimientos](#18-historial-de-movimientos-rf-06)
19. [Débito Automático](#19-débito-automático-de-cuotas)
20. [Scripts de generación de datos](#20-scripts-de-generación-de-datos)

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
├── domain/                  #  Capa de dominio (Hexagonal - IMPLEMENTADO)
│   ├── entities.py           #   Entidades de negocio puras (dataclases)
│   ├── ports.py              #   Interfaces abstractas (RepositorioCuenta, etc.)
│   └── rules.py             #   Reglas de negocio: validar_saldo, simular_cuotas
│
├── application/              #  Casos de uso (Hexagonal - IMPLEMENTADO)
│   └── use_cases.py          #   RealizarTransferencia, SolicitarPrestamo, PagarCuota
│
├── infrastructure/            #  App Django principal
│   ├── models.py              #   Modelos de base de datos
│   │                          #   (Cliente, Cuenta, Transaccion,
│   │                          #    Tarjeta, Prestamo, CuotaPrestamo,
│   │                          #    ConfiguracionSeguridad, AlertaFraude)
│   ├── forms.py               #   Formulario de registro de clientes
│   ├── auth_views.py          #   Vistas (login, registro, dashboard,
│   │                          #    transferencia, préstamos)
│   ├── signals.py             #   Señales (crear Cliente al crear User)
│   ├── apps.py                #   Configuración de la app
│   ├── management/             #   Comandos personalizados de Django
│   │   └── commands/
│   │       └── pagar_cuotas_vencidas.py  # Débito automático de cuotas
│   ├── adapters/              #   Adaptadores hexagonales (IMPLEMENTADOS)
│   │   ├── __init__.py
│   │   └── repositories.py    #   DjangoCuentaRepository, etc.
│   └── migrations/            #   Historial de cambios en la DB
│
├── templates/               #  Plantillas HTML
│   ├── base.html            #   Plantilla base (header, nav, footer, skip link)
│   ├── inicio.html          #   Landing page (página de bienvenida)
│   ├── login.html           #   Inicio de sesión
│   ├── registro.html        #   Registro de nuevo cliente
│   ├── dashboard.html       #   Panel principal del cliente
│   ├── transferencia.html   #   Formulario de transferencia
│   ├── transferencia_exito.html  #  Confirmación de transferencia
│   └── prestamos/           #   Vistas de préstamos
│       ├── lista.html       #     Lista de préstamos del cliente
│       ├── solicitar.html   #     Simulación y solicitud
│       └── detalle.html     #     Detalle y pago de cuotas
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

Cuando un usuario escribe una URL en el navegador, pasan varias cosas antes de que vea la página. Veamos el ejemplo de cuando alguien entra a `/inicio-sesion/`:

```
 PASO 1                          PASO 2                          PASO 3
┌──────────────┐           ┌──────────────┐           ┌──────────────────┐
│ Usuario      │  escribe  │  Django      │  busca en  │  config/urls.py  │
│ escribe      │ ────────> │  recibe el   │ ────────> │                  │
│ /inicio-sesion/      │           │  pedido      │           │  'login/' →      │
│              │           │              │           │  InicioSesionView       │
└──────────────┘           └──────────────┘           └────────┬─────────┘
                                                               │
                                                               ▼
 PASO 4                          PASO 5                          PASO 6
┌──────────────────────┐    ┌───────────────┐            ┌───────────────┐
│ InicioSesionView            │    │  InicioSesionView     │            │  Django       │
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

1. **El navegador** hace un pedido (request) a `http://localhost:8000/inicio-sesion/`
2. **Django** recibe el pedido y busca qué hacer con esa URL
3. **`urls.py`** es como una guía telefónica: dice "cuando alguien entre a `login/`, ejecutá la vista `InicioSesionView`"
4. **La vista `InicioSesionView`** se ejecuta. Si es un GET (entrar a la página), muestra el formulario vacío. Si es un POST (enviar el formulario), valida los datos.
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
from infrastructure.auth_views import InicioView, RegistroView, InicioSesionView, PanelView, TransferenciaView

urlpatterns = [
    path('', InicioView.as_view(), name='inicio'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('inicio-sesion/', InicioSesionView.as_view(), name='inicio_sesion'),
    path('cerrar-sesion/', LogoutView.as_view(next_page='inicio'), name='cerrar_sesion'),
    path('panel/', PanelView.as_view(), name='panel'),
    path('transferencia/', TransferenciaView.as_view(), name='transferencia'),
    path('prestamos/', PrestamoListView.as_view(), name='prestamos'),
    path('prestamos/solicitar/', PrestamoCrearView.as_view(), name='prestamos_solicitar'),
    path('prestamos/<int:pk>/', PrestamoDetalleView.as_view(), name='prestamo_detalle'),
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
| `/` | `InicioView` | `inicio.html` | No | Landing page. Si ya estás logueado, redirige al panel |
| `/registro/` | `RegistroView` | `registro.html` | No | Muestra formulario de alta. Al enviar, crea usuario y redirige al panel |
| `/inicio-sesion/` | `InicioSesionView` | `login.html` | No | Muestra formulario de login. Al enviar, inicia sesión y redirige al panel |
| `/cerrar-sesion/` | `LogoutView` | — | Sí | Cierra la sesión (POST con CSRF) y redirige al inicio |
| `/panel/` | `PanelView` | `dashboard.html` | **Sí** | Muestra saldos, cuentas, movimientos y préstamos activos |
| `/transferencia/` | `TransferenciaView` | `transferencia.html` | **Sí** | Muestra formulario de transferencia. Al enviar, ejecuta caso de uso hexagonal |
| `/prestamos/` | `PrestamoListView` | `prestamos/lista.html` | **Sí** | Lista todos los préstamos del cliente |
| `/prestamos/solicitar/` | `PrestamoCrearView` | `prestamos/solicitar.html` | **Sí** | Simula y solicita un nuevo préstamo |
| `/prestamos/<id>/` | `PrestamoDetalleView` | `prestamos/detalle.html` | **Sí** | Detalle del préstamo y pago de cuotas |

> 💡 **Concepto clave:** Las rutas marcadas con **"Sí"** en "¿Requiere login?" usan `LoginRequiredMixin`. Si un usuario no logueado intenta entrar, Django lo redirige automáticamente a `/inicio-sesion/`.

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
            return redirect('panel')
        return super().dispatch(request, *args, **kwargs)
```

**¿Qué hace?**
- `TemplateView` es la vista más simple de Django: solo muestra un template HTML
- `template_name = 'inicio.html'` le dice a Django qué archivo HTML usar
- `dispatch()` se ejecuta **siempre**, antes que cualquier otro método:
  - Si el usuario **ya está logueado** (`request.user.is_authenticated`), lo redirige al panel
  - Si **no está logueado**, muestra la landing page normalmente

**Ejemplo concreto:** Si un usuario logueado escribe `/` en el navegador, automáticamente va a parar a `/panel/`.

---

### RegistroView

```python
class RegistroView(CreateView):
    form_class = RegistroClienteForm
    template_name = 'registro.html'
    success_url = reverse_lazy('panel')

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
5. `redirect()`: redirige al panel

---

### InicioSesionView

```python
class InicioSesionView(BaseLoginView):
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
- Redirigir al panel

---

### PanelView

```python
class PanelView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cliente = self.request.user.cliente
        cuentas = cliente.cuentas.all()
        cuentas_ids = list(cuentas.values_list('id', flat=True))
        transacciones = Transaccion.objects.filter(
            Q(cuenta_origen__in=cuentas) | Q(cuenta_destino__in=cuentas)
        ).order_by('-fecha_creacion')[:10]
        prestamos = Prestamo.objects.filter(cliente=cliente).order_by('-fecha_inicio')[:5]

        context['cliente'] = cliente
        context['cuentas'] = cuentas
        context['cuentas_ids'] = cuentas_ids
        context['transacciones'] = transacciones
        context['prestamos'] = prestamos
        return context
```

**¿Qué hace?**
- `LoginRequiredMixin`: si el usuario no está logueado, lo redirige al login automáticamente
- `get_context_data()`: consulta la base de datos real (ya no usa datos mock). Obtiene el Cliente, sus Cuentas, las últimas 10 Transacciones y sus Préstamos activos.
- El dashboard muestra alias, CVU, saldo, movimientos con signo (+entrada / -salida) y una sección de préstamos.

---

### TransferenciaView (POST usa hexagonal)

```python
class TransferenciaView(LoginRequiredMixin, TemplateView):
    template_name = 'transferencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuentas'] = self.request.user.cliente.cuentas.filter(estado='activa')
        return context

    def post(self, request, *args, **kwargs):
        # Parsea la entrada del formulario...
        with transaction.atomic():
            repo_cuenta = DjangoCuentaRepository()
            repo_tx = DjangoTransaccionRepository()
            caso = RealizarTransferencia(repo_cuenta, repo_tx)
            resultado = caso.ejecutar(origen_id, destino_raw, monto, concepto)
        # ...
```

**¿Qué hace diferente?**
- **GET**: muestra las cuentas activas del cliente desde la DB real
- **POST**: usa el **caso de uso hexagonal** `RealizarTransferencia` en lugar de manipular el ORM directamente. La lógica de negocio (validar saldo, cuenta destino, transferir) está en `application/use_cases.py` y `domain/rules.py`, separada de Django.
- La transferencia busca la cuenta destino por **alias, CVU, número de cuenta o ID**.

---

### PrestamoListView

```python
class PrestamoListView(LoginRequiredMixin, ListView):
    template_name = 'prestamos/lista.html'
    context_object_name = 'prestamos'

    def get_queryset(self):
        return Prestamo.objects.filter(
            cliente=self.request.user.cliente
        ).order_by('-fecha_inicio')
```

**¿Qué hace?** Lista todos los préstamos del cliente autenticado, del más reciente al más antiguo. Cada préstamo muestra: monto original, saldo pendiente, sistema de amortización y estado.

---

### PrestamoCrearView (solicitar préstamo)

```python
class PrestamoCrearView(LoginRequiredMixin, TemplateView):
    template_name = 'prestamos/solicitar.html'

    def post(self, request, *args, **kwargs):
        accion = request.POST.get('accion', '')
        # ...
        if accion == 'simular':
            use_case = SolicitarPrestamo(repo_prestamo, repo_cuenta)
            cuotas = use_case.simular(monto, plazo, sistema)
            # Muestra la tabla de cuotas simuladas (francés o alemán)

        elif accion == 'confirmar':
            use_case = SolicitarPrestamo(repo_prestamo, repo_cuenta)
            prestamo, mensaje = use_case.ejecutar(cliente_id, monto, plazo, sistema)
            # Crea el préstamo y acredita el monto en la cuenta
```

**Flujo:** El usuario ingresa monto, plazo y sistema (francés/alemán) → presiona "Simular" → ve tabla de cuotas con interés y amortización → presiona "Confirmar" → se crea el préstamo y se acredita el monto.

---

### PrestamoDetalleView (pagar cuotas)

```python
class PrestamoDetalleView(LoginRequiredMixin, DetailView):
    template_name = 'prestamos/detalle.html'

    def post(self, request, *args, **kwargs):
        # Pago de cuota individual con PagarCuota (caso de uso hexagonal)
        use_case = PagarCuota(repo_prestamo, repo_cuenta)
        ok, mensaje = use_case.ejecutar(cuota_id, cuenta_id, cliente_id)
```

**¿Qué hace?** Muestra el detalle del préstamo con tabla de cuotas (número, monto, vencimiento, estado). Cada cuota pendiente tiene un botón "Pagar" que debita de la cuenta seleccionada y marca la cuota como pagada. Actualiza el saldo pendiente del préstamo.

---

### ¿Cómo encajan las vistas con la arquitectura hexagonal?

```
┌──────────────────────────┐     ┌───────────────────────────┐     ┌──────────────────────┐
│ Django View (MTV)       │────>│ Caso de Uso (Application)  │────>│ Puerto (Interface)    │
│ TransferenciaView POST  │     │ RealizarTransferencia      │     │ RepositorioCuenta    │
│ PrestamoCrearView POST  │     │ SolicitarPrestamo          │     │ RepositorioPrestamo  │
│ PrestamoDetalleView POST│     │ PagarCuota                 │     │                      │
└──────────────────────────┘     └───────────────────────────┘     └──────────┬───────────┘
                                                                            │
                                                                            ▼
                                                              ┌──────────────────────────┐
                                                              │ Adaptador (Infraest.)    │
                                                              │ DjangoCuentaRepository   │
                                                              │ Implementa el puerto     │
                                                              │ usando Django ORM +      │
                                                              │ select_for_update()      │
                                                              └──────────────────────────┘
```

Las vistas de **registro, login y dashboard** usan MTV clásico (no pasan por casos de uso, solo consultan el ORM directamente). Las vistas de **transferencia y préstamos** usan hexagonal: la vista recibe datos del formulario, instancia el caso de uso, y éste orquesta puertos y adaptadores.

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
        <a href="{% url 'cerrar_sesion' %}">Cerrar sesión</a>
      {% else %}
        <a href="{% url 'inicio_sesion' %}">Iniciar sesión</a>
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
| `{% url 'inicio_sesion' %}` | Genera la URL de la ruta llamada 'inicio_sesion' |
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

Las vistas pasan datos a los templates a través de un diccionario. Por ejemplo, en `PanelView`:

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

    dni = models.CharField(
        max_length=8, unique=True,
        validators=[RegexValidator(r'^\d{7,8}$', 'El DNI debe tener 7 u 8 dígitos numéricos.')],
        help_text="Documento Nacional de Identidad (7 u 8 dígitos)"
    )

    telefono = models.CharField(max_length=20, blank=True, default='')
    direccion = models.TextField(blank=True, default='')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='activo')

    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO, default='N')
    profesion = models.CharField(max_length=100, blank=True, verbose_name="Ocupación/Profesión")
    ingreso_mensual = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                          verbose_name="Ingreso mensual estimado")
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
    numero_cuenta = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    alias = models.CharField(max_length=20, unique=True, null=True, blank=True)
    cvu = models.CharField(max_length=22, unique=True, null=True, blank=True)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    moneda = models.CharField(max_length=3, default='ARS')
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CUENTA, default='activa')
    limite_transferencia_diario = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)

    class Meta:
        ordering = ['-fecha_apertura']

    def save(self, *args, **kwargs):
        if not self.numero_cuenta:
            self.numero_cuenta = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cuenta {self.numero_cuenta} - {self.cliente.usuario.username}"
```

**Campo por campo:**

| Campo | Tipo | ¿Qué guarda? |
|---|---|---|
| `cliente` | ForeignKey(Cliente) | ¿De quién es esta cuenta? `related_name='cuentas'` permite hacer `cliente.cuentas.all()` |
| `tipo_cuenta` | CharField(choices) | "ahorro" o "corriente" |
| `numero_cuenta` | CharField(20, unique) | Número único de 12 caracteres generado automáticamente con UUID |
| `alias` | CharField(20, unique, null) | Nombre corto definido por el usuario para identificar la cuenta (ej: "mi.sueldo") |
| `cvu` | CharField(22, unique, null) | Clave Virtual Uniforme de 22 dígitos (estándar BCRA) |
| `saldo` | DecimalField(12,2) | Dinero disponible. 12 dígitos, 2 decimales. |
| `moneda` | CharField(3) | ARS (pesos) o USD (dólares). Por defecto ARS. |
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

    cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='tarjetas')
    tipo_tarjeta = models.CharField(max_length=20, choices=TIPO_TARJETA)
    numero = models.CharField(
        max_length=16, unique=True,
        validators=[RegexValidator(r'^\d{16}$', 'El número de tarjeta debe tener exactamente 16 dígitos.')]
    )
    fecha_expiracion = models.DateField()
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, choices=ESTADO_TARJETA, default='activa')

    class Meta:
        verbose_name = 'Tarjeta'
        verbose_name_plural = 'Tarjetas'
        ordering = ['-fecha_expiracion']
```

| Campo | Tipo | ¿Qué guarda? |
|---|---|---|
| `cuenta` | ForeignKey(Cuenta) | A qué cuenta está asociada la tarjeta |
| `numero` | CharField(16, unique) | Número de tarjeta de 16 dígitos (validado con regex) |
| `limite_credito` | DecimalField(12,2) | Límite de crédito (solo para tarjetas de crédito) |
| `saldo_actual` | DecimalField(12,2) | Saldo disponible o deuda actual |

> ⚠️ **Cambio importante:** Se eliminó el campo `cvv` porque el estándar **PCI DSS** prohíbe almacenar códigos de seguridad de tarjetas, incluso en bases de datos de desarrollo. También se cambió `CASCADE` por `PROTECT` en la relación con Cuenta: no se puede borrar una cuenta que tenga tarjetas asociadas.

---

### Modelo Prestamo

```python
class Prestamo(models.Model):
    ESTADO_PRESTAMO = [('activo', 'Activo'), ('pagado', 'Pagado'), ('vencido', 'Vencida/Mora')]
    SISTEMA_AMORTIZACION = [('frances', 'Francés'), ('aleman', 'Alemán')]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='prestamos')
    monto_original = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_interes_anual = models.FloatField()
    plazo_meses = models.IntegerField()
    sistema_amortizacion = models.CharField(max_length=20, choices=SISTEMA_AMORTIZACION, default='frances')
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
    fecha_pago = models.DateField(null=True, blank=True)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
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

### Correcciones y mejoras aplicadas a los modelos

#### 🔴 Eliminación de `cvv` en Tarjeta

El campo `cvv` guardaba el código de seguridad de la tarjeta en texto plano. **El estándar PCI DSS prohíbe almacenar CVV**, incluso en entornos de desarrollo. Se eliminó porque:
- Si el repo se filtra, los CVV quedan expuestos
- Es ilegal almacenarlos sin certificación PCI DSS
- Django no puede hashearlos (se necesitan en cada transacción)

#### 🟡 `CASCADE` reemplazado por `PROTECT` en Tarjeta

```python
# Antes (inseguro):
cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)

# Después (seguro):
cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT)
```

Con `CASCADE`, si se borraba una cuenta se eliminaban todas sus tarjetas automáticamente. Con `PROTECT`, Django impide borrar una cuenta que tenga tarjetas asociadas. Es la misma protección que se usa en `Cuenta.cliente` y `Prestamo.cliente`.

#### 🟡 Validadores con `RegexValidator`

```python
# dni: solo 7 u 8 dígitos numéricos (en modelo Y formulario)
validators=[RegexValidator(r'^\d{7,8}$', 'El DNI debe tener 7 u 8 dígitos numéricos.')]

# numero de tarjeta: exactamente 16 dígitos (en el modelo)
validators=[RegexValidator(r'^\d{16}$', 'El número de tarjeta debe tener exactamente 16 dígitos.')]
```

El validador de DNI se duplicó **tanto en el modelo como en el formulario** porque Django no ejecuta los validadores del modelo automáticamente al llamar a `save()`. En el formulario se ejecutan durante `is_valid()`, antes de tocar la base de datos. En el modelo sirven como red de seguridad si se crean clientes desde el admin o la shell.

#### 🟡 `dni` ahora es realmente obligatorio

```python
# Antes (peligroso):
dni = models.CharField(max_length=8, unique=True, default='')

# Después (correcto):
dni = models.CharField(max_length=8, unique=True, validators=[...])
```

Con `default=''` y `unique=True`, dos clientes sin DNI (ej: creados por la señal o desde el admin) causaban un error de unicidad porque ambos tendrían `dni=''`. Ahora es obligatorio siempre.

#### 🟡 `ingreso_mensual` distingue "no especificó" de "cero pesos"

```python
# Antes:
ingreso_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

# Después:
ingreso_mensual = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
```

Con `default=0.00`, un cliente que no completó el campo quedaba registrado con ingreso $0, confundiéndose con alguien que realmente no tiene ingresos. Con `null=True`, queda como `NULL` en la DB, que significa "desconocido".

#### 🟡 `verbose_name` y `verbose_name_plural` en español

Se agregaron a todos los modelos que faltaban (`ConfiguracionSeguridad`, `Tarjeta`, `Prestamo`, `CuotaPrestamo`, `AlertaFraude`). En el admin de Django ahora se muestran como "Tarjetas", "Préstamos", "Alertas de fraude" en vez de los nombres inglés por defecto.

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
                           validators=[RegexValidator(r'^\d{7,8}$',
                                                      'El DNI debe tener 7 u 8 dígitos numéricos.')],
                           help_text='Documento Nacional de Identidad (7 u 8 dígitos)')
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
import uuid
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Cliente, Cuenta, ConfiguracionSeguridad

@receiver(post_save, sender=User)
def crear_perfil_cliente(sender, instance, created, **kwargs):
    if created:
        dni_temporal = uuid.uuid4().hex[:8]
        cliente = Cliente.objects.create(usuario=instance, dni=dni_temporal)
        Cuenta.objects.create(cliente=cliente, tipo_cuenta='ahorro', moneda='ARS')
        ConfiguracionSeguridad.objects.create(cliente=cliente)
```

**¿Qué hace ahora (versión actualizada)?**
- **Cliente**: crea con un DNI temporal único (UUID de 8 caracteres). El formulario de registro pisa este DNI con el real después.
- **Cuenta**: crea automáticamente una cuenta de ahorro en pesos (el `numero_cuenta` se autogenera en `save()`).
- **ConfiguracionSeguridad**: crea la configuración de seguridad por defecto (sin 2FA, sin bloqueo).

**Flujo completo:**

```
1. Alguien crea un User (desde el registro, desde el admin, desde la terminal)
2. Django guarda el User en la base de datos
3. Inmediatamente después, Django ejecuta la señal
4. La señal crea un Cliente (con DNI temporal), una Cuenta (ahorro en ARS) y una ConfiguracionSeguridad
5. Si el User se creó desde el formulario de registro, el formulario completa los datos del Cliente (DNI real, teléfono, etc.)
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

## 11. Datos Reales (antes Mock)

### Consultas reales a la base de datos

En versiones anteriores se usaban datos mock (inventados) para simular el funcionamiento. A partir de la versión actual, **todas las vistas usan consultas reales a la base de datos**:

- **Dashboard**: consulta el `Cliente`, sus `Cuentas`, `Transacciones` y `Prestamos` desde PostgreSQL
- **Transferencia**: crea `Transaccion` reales, actualiza saldos con `select_for_update` y `transaction.atomic`
- **Préstamos**: crea `Prestamo` y `CuotaPrestamo` en la DB, realiza pagos reales

El template sigue siendo compatible con ambas fuentes gracias a `@property nombre` en el modelo `Cliente`.

### Cómo funciona ahora

```python
class PanelView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.request.user.cliente
        cuentas = cliente.cuentas.all()
        transacciones = Transaccion.objects.filter(
            Q(cuenta_origen__in=cuentas) | Q(cuenta_destino__in=cuentas)
        ).order_by('-fecha_creacion')[:10]
        prestamos = Prestamo.objects.filter(cliente=cliente)[:5]
        context['cliente'] = cliente
        context['cuentas'] = cuentas
        context['transacciones'] = transacciones
        context['prestamos'] = prestamos
        return context
```

### ¿Por qué funciona `{{ cliente.nombre }}` en el template? Porque agregamos la **propiedad** `nombre` en el modelo `Cliente`:

```python
@property
def nombre(self):
    return self.usuario.first_name or self.usuario.username
```

Esto permite que `cliente.nombre` funcione directamente desde la instancia real del modelo `Cliente` sin necesidad de datos mock.

**Diferencia clave:** Los datos ya se obtienen de la base de datos real mediante consultas ORM y casos de uso hexagonales. La lógica de negocio (transferencias, préstamos) está en `domain/rules.py` y `application/use_cases.py`, separada de Django.

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

**En nuestro proyecto (implementado):**

| Capa | ¿Qué va acá? | ¿Depende de Django? |
|---|---|---|
| **Domain** (dominio) | Entidades: `CuentaEntity`, `TransaccionEntity`, `PrestamoEntity` | ❌ No |
| **Domain/ports** | Interfaces: `RepositorioCuenta(ABC)`, `RepositorioTransaccion(ABC)` | ❌ No |
| **Domain/reglas** | Funciones: `validar_saldo_suficiente()`, `simular_cuotas_frances()` | ❌ No |
| **Application** | Casos de uso: `RealizarTransferencia.ejecutar()`, `SolicitarPrestamo.ejecutar()` | ❌ No |
| **Infrastructure/adapters** | `DjangoCuentaRepository`, `DjangoTransaccionRepository` | ✅ Sí (usa Django ORM) |
| **Infrastructure/views** | Vistas que conectan el navegador con los casos de uso | ✅ Sí |

**Ventaja:** Si mañana cambiamos de PostgreSQL a MySQL, solo tocamos el adaptador. La lógica de negocio (domain + application) no se modifica. Ni siquiera sabe qué base de datos se usa.

### 12.2 ¿Por qué híbrido y no hexagonal puro?

Decidimos ser **pragmáticos**: usar Django donde ya es fuerte, e implementar hexagonal donde la lógica de negocio lo requiere.

| Módulo | Arquitectura | ¿Por qué esta decisión? |
|---|---|---|
| **Registro / Login** | MTV clásico de Django | Django tiene años de auditoría de seguridad en autenticación: hasheo de contraseñas con PBKDF2, protección contra timing attacks, CSRF, sesiones seguras. |
| **Dashboard** | MTV clásico | Es solo mostrar información. Se consulta el ORM directamente para lectura. |
| **Transferencias** | **Hexagonal** | La lógica está en `RealizarTransferencia` (application) y usa puertos (`RepositorioCuenta`) implementados con `select_for_update`. La lógica de negocio está separada de Django. |
| **Préstamos** | **Hexagonal** | `SolicitarPrestamo` y `PagarCuota` usan `RepositorioPrestamo` vía adaptadores. `simular_cuotas_frances()` y `simular_cuotas_aleman()` son funciones puras en `domain/rules.py` sin dependencias. |
| **Detección de fraude** (futuro) | **Hexagonal** | Poder cambiar entre Scikit-learn y PyTorch sin tocar la lógica de negocio. |

### 12.3 ¿Qué ventajas nos da cada cosa de Django?

| Feature de Django | Si lo hiciéramos con un adaptador propio... | Ventaja de usar Django |
|---|---|---|
| **`UserCreationForm`** | Tendríamos que validar contraseñas, hashear con PBKDF2, verificar que no sea una contraseña común, proteger contra timing attacks | Django ya lo hace, auditado por miles de desarrolladores |
| **`InicioSesionView`** | Manejar sesiones, cookies, expiración, redirección post-login | Django gestiona sesiones seguras con cookies firmadas |
| **`@login_required`** | Verificar en cada request si el usuario tiene sesión activa | Una línea de código protege toda una vista |
| **CSRF token** | Generar token único, verificar en cada POST, rotar tokens | Django lo hace automáticamente con `{% csrf_token %}` |
| **ORM** | Escribir SQL a mano, escapando inputs para evitar SQL injection | El ORM genera SQL parametrizado, immune a SQL injection |
| **`messages`** | Guardar notificaciones en sesión, mostrarlas una vez y borrarlas | Django maneja el ciclo de vida completo |
| **`transaction.atomic()`** | Manejar manualmente BEGIN/COMMIT/ROLLBACK | Garantiza atomicidad: si algo falla, todo se revierte |

### 12.4 Así funciona hoy el hexagonal

El flujo de una transferencia sigue este camino:

```
                    ┌───────────────────────────────────────┐
                    │           Vista Django                 │
                    │  TransferenciaView (POST)              │
                    │  Recibe los datos del formulario       │
                    │  Envuelve en transaction.atomic()      │
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
        │  Adaptador Django    │              │  Adaptador Django    │
        │  DjangoCuentaRepo    │              │  DjangoTxRepo        │
        │                       │              │                      │
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

1. Las **reglas de negocio** (`domain/rules.py`) se prueban sin base de datos — son funciones puras
2. Los **casos de uso** (`application/use_cases.py`) se prueban con mocks — no necesitan Django
3. Los **adaptadores** (`infrastructure/adapters/repositories.py`) son delgados — solo conectan el ORM con los puertos
4. Si cambiamos de base de datos o de framework web, la lógica de negocio no se toca

### 12.5 Estructura real de los archivos hexagonales

#### `domain/entities.py` — Dataclases puras (sin Django)

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class CuentaEntity:
    id: int
    cliente_id: int
    tipo_cuenta: str
    numero_cuenta: str
    alias: Optional[str]
    cvu: Optional[str]
    saldo: Decimal = Decimal('0.00')
    moneda: str = 'ARS'
    estado: str = 'activa'

@dataclass
class PrestamoEntity:
    id: int
    cliente_id: int
    monto_original: Decimal
    saldo_pendiente: Decimal
    tasa_interes_anual: float
    plazo_meses: int
    sistema_amortizacion: str = 'frances'
    cuotas: List[CuotaEntity] = field(default_factory=list)
```

Son clases Python normales. No heredan de `models.Model`. No tocan la base de datos.

#### `domain/ports.py` — Interfaces (ABCs)

```python
from abc import ABC, abstractmethod

class RepositorioCuenta(ABC):
    @abstractmethod
    def buscar_por_id_con_bloqueo(self, cuenta_id: int) -> CuentaEntity: ...
    
    @abstractmethod
    def buscar_por_alias_o_cvu(self, valor: str) -> Optional[CuentaEntity]: ...
    
    @abstractmethod
    def incrementar_saldo(self, cuenta_id: int, delta: Decimal) -> None: ...
```

Define **qué operaciones** existen, sin decir **cómo** se implementan. Es un contrato.

#### `domain/rules.py` — Lógica de negocio pura

```python
def simular_cuotas_frances(monto: Decimal, tasa_anual: float, plazo_meses: int):
    """Calcula cuotas con sistema francés (cuota fija)."""
    tasa_mensual = Decimal(str(tasa_anual / 12))
    cuota_fija = monto * tasa_mensual * (1 + tasa_mensual) ** plazo / (...)
    for i in range(1, plazo_meses + 1):
        interes = saldo * tasa_mensual
        amortizacion = cuota_fija - interes
        saldo -= amortizacion
        yield CuotaSimulada(numero=i, monto=cuota_fija, interes=interes, ...)
```

No usa Django, no usa base de datos. Es una función pura: dado un input, devuelve un output.

#### `application/use_cases.py` — Orquestadores

```python
class RealizarTransferencia:
    def __init__(self, repo_cuenta: RepositorioCuenta, repo_tx: RepositorioTransaccion):
        self._repo_cuenta = repo_cuenta  # Puerto (no sabe cómo se implementa)
        self._repo_tx = repo_tx
    
    def ejecutar(self, origen_id, destino_busqueda, monto, descripcion):
        # 1. Validar reglas (domain/rules.py)
        # 2. Buscar cuentas (a través del puerto)
        # 3. Actualizar saldos
        # 4. Registrar transacción
        return ResultadoTransferencia(exitoso=True, mensaje='...')
```

El caso de uso **no sabe si los datos vienen de PostgreSQL o de un mock**. Solo conoce la interfaz (`RepositorioCuenta`).

#### `infrastructure/adapters/repositories.py` — Implementaciones Django

```python
class DjangoCuentaRepository(RepositorioCuenta):
    def buscar_por_id_con_bloqueo(self, cuenta_id: int):
        c = Cuenta.objects.select_for_update().get(id=cuenta_id)
        return _cuenta_a_entity(c)  # Convierte modelo Django → dataclass
    
    def incrementar_saldo(self, cuenta_id: int, delta: Decimal):
        Cuenta.objects.filter(id=cuenta_id).update(saldo=F('saldo') + delta)
```

Acá sí se usa Django ORM. Pero solo en esta capa. El dominio no sabe que Django existe.

---

## 13. Cómo ejecutar el sistema

### Requisitos

- **Python** 3.10+
- **PostgreSQL** (local o Neon)
- `.env` configurado

### Pasos

```bash
# 1. Activar entorno virtual
& ".venv\Scripts\Activate.ps1"   # Windows PowerShell
source .venv/bin/activate         # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Migrar base de datos
python manage.py migrate

# 4. Iniciar servidor
python manage.py runserver

# 5. Abrir en navegador
# http://localhost:8000
```

### Flujo de prueba

1. Entrá a `http://localhost:8000/registro/` — creá un usuario
2. Te redirige al panel con tu cuenta de ahorro en pesos
3. Registrá un segundo usuario desde otra pestaña/incógnito
4. Volvé al primero, entrá a `/transferencia/` — transferí al número/alias/CVU del segundo
5. Entrá a `/prestamos/solicitar/` — simulá un préstamo (francés o alemán), confirmalo
6. En `/prestamos/` y luego `/prestamos/<id>/` pagá cuotas individuales

---

## 14. Glosario Django

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
| **Management Command** | Comando personalizado que se ejecuta con `python manage.py <nombre>`. Django busca automáticamente archivos `.py` dentro de `app/management/commands/` y los registra como comandos. Ej: `python manage.py pagar_cuotas_vencidas` |
| **`python manage.py`** | Herramienta de línea de comandos de Django. Comandos comunes: `runserver`, `check`, `makemigrations`, `migrate`, y cualquier **Management Command** que hayas creado |
| **`settings.py`** | Archivo de configuración global: apps instaladas, base de datos, zona horaria, rutas de archivos |

---

---

## 15. Concurrencia en Transferencias

### ¿Por qué es importante?

Imaginá que tenés $10.000 en tu cuenta y hacés dos transferencias de $8.000 al mismo tiempo:

```
Sin concurrencia:
  Transferencia 1: lee saldo ($10.000) → descuenta $8.000 → guarda ($2.000)
  Transferencia 2: lee saldo ($10.000) → descuenta $8.000 → guarda ($2.000)
  ✗ Resultado: te quedan $2.000, pero gastaste $16.000. El banco perdió $6.000.
  
Con concurrencia (select_for_update):
  Transferencia 1: BLOQUEA la cuenta → lee saldo ($10.000) → descuenta → guarda ($2.000) → LIBERA
  Transferencia 2: ESPERA → cuando se libera, lee saldo ($2.000) → saldo insuficiente → RECHAZA
  ✓ Resultado: una transferencia se realiza, la otra se rechaza. Correcto.
```

### Cómo lo implementamos

```python
# En el adaptador DjangoCuentaRepository (repositories.py)
def buscar_por_id_con_bloqueo(self, cuenta_id: int):
    return Cuenta.objects.select_for_update().get(id=cuenta_id)
```

`select_for_update()` es un bloqueo pesimista a nivel de base de datos. Cuando una transacción obtiene el bloqueo de una fila, **ninguna otra transacción puede leer ni modificar esa fila** hasta que la primera termine.

### Doble bloqueo ordenado por ID (evita deadlocks)

Cuando una transferencia involucra dos cuentas (origen y destino), necesitamos bloquear ambas. Pero si dos transferencias bloquean las cuentas en orden inverso, se produce un **deadlock**:

```
Transferencia A: BLOQUEA cuenta 1 → necesita cuenta 2 (espera)
Transferencia B: BLOQUEA cuenta 2 → necesita cuenta 1 (espera)
✗ Ambas esperan para siempre. Deadlock.
```

Solución: **bloquear siempre en orden ascendente de IDs**:

```python
# En RealizarTransferencia.ejecutar()
ids = sorted([cuenta_origen_id, destino.id])  # Orden ascendente
origen = repo_cuenta.buscar_por_id_con_bloqueo(ids[0])
destino = repo_cuenta.buscar_por_id_con_bloqueo(ids[1])
```

Si siempre bloqueamos los IDs de menor a mayor, nunca habrá bloqueos circulares.

### Updates atómicos con F()

Para operaciones que solo modifican saldos (sin leer el valor anterior), usamos `F()` expressions:

```python
Cuenta.objects.filter(id=cuenta_id).update(saldo=F('saldo') + delta)
```

`F('saldo')` se refiere al valor actual de la columna `saldo` en la base de datos. Django genera SQL como `UPDATE cuenta SET saldo = saldo + 100 WHERE id = 1`. Esto es atómico a nivel de base de datos: no hay race condition entre leer y escribir.

### Management command de débito automático

El comando `pagar_cuotas_vencidas` usa `select_for_update()` para procesar cuotas:

```python
for cuota in cuotas_vencidas:
    with transaction.atomic():
        cuenta = Cuenta.objects.select_for_update().get(id=cuenta.id)
        if cuenta.saldo >= cuota.monto_cuota:
            Cuenta.objects.filter(id=cuenta.id).update(saldo=F('saldo') - cuota.monto_cuota)
```

Cada cuota se procesa en su propia transacción atómica. Si el saldo es insuficiente, salta esa cuota y sigue con la siguiente.

---

## 16. Machine Learning en el Sistema

El sistema integra dos modelos de Machine Learning usando la arquitectura hexagonal (puertos y adaptadores):

### 16.1 RF-07: Detección de Fraude (Isolation Forest)

**Problema:** Detectar transferencias sospechosas en tiempo real.

**Enfoque:** Aprendizaje no supervisado (anomaly detection). El modelo aprende **qué es normal** en las transacciones y marca lo que se desvía.

**Features (características):**

| Feature | Descripción |
|---|---|
| `monto` | Monto de la transferencia |
| `hora` | Hora del día (0-23) |
| `dia_semana` | Día de la semana (0-6) |
| `saldo_origen` | Saldo de la cuenta de origen |

**Entrenamiento:** 6.215 transacciones normales + 100 anomalías sintéticas. Accuracy: **97.3%**

**Arquitectura (puerto y adaptador):**

```
domain/ports.py:MotorFraud(ABC)          ← Puerto (interfaz)
    └── evaluar(monto, hora, dia_semana, ...) → float

infrastructure/adapters/fraude_adapter.py  ← Adaptador
    └── evaluar_transferencia(monto, cuenta_id) → score 0-1

application/use_cases.py:RealizarTransferencia  ← Integración
    └── Si score ≥ 0.7 → crea AlertaFraude
```

**Integración:** Cada transferencia que se realiza en el sistema pasa por el modelo. Si el score de riesgo supera 0.7, se crea un registro en `AlertaFraude` visible en `/admin/`.

### 16.2 RF-15: Scoring Crediticio (Random Forest)

**Problema:** Evaluar automáticamente si un cliente es buen pagador antes de aprobarle un préstamo.

**Enfoque:** Aprendizaje supervisado. Se entrena con 223 clientes que ya tienen préstamos, etiquetados como "buen pagador" (pagó siempre a tiempo) o "mal pagador" (2+ cuotas vencidas).

**Features:**

| Feature | Descripción |
|---|---|
| `edad` | Edad del cliente |
| `ingreso` | Ingreso mensual estimado |
| `educacion` | Nivel educativo (1-5) |
| `score_inicial` | Score crediticio al registrarse |
| `antiguedad` | Días desde el registro |
| `cant_prestamos` | Cantidad de préstamos tomados |
| `genero` | Codificado one-hot |

**Arquitectura:**

```
domain/ports.py:MotorScoring(ABC)        ← Puerto
    └── evaluar(cliente_id) → float (0=bajo riesgo, 1=alto riesgo)

infrastructure/adapters/scoring_adapter.py  ← Adaptador
    └── evaluar_cliente(cliente_id) → score 0-1

application/use_cases.py:SolicitarPrestamo  ← Integración
    └── Si score ≥ 0.5 → rechaza préstamo
```

**Comportamiento:**

| Cliente | Score | Resultado |
|---|---|---|
| Pagador puntual (sin vencidas) | ~0.16 | ✅ Préstamo aprobado |
| Moroso (3 cuotas vencidas) | ~0.94 | ❌ Préstamo rechazado |

### 16.3 Scripts de entrenamiento

| Script | Modelo | Uso |
|---|---|---|
| `scripts/entrenar_fraude.py` | Isolation Forest | `python scripts/entrenar_fraude.py` |
| `scripts/entrenar_scoring.py` | Random Forest | `python scripts/entrenar_scoring.py` |

Ambos scripts leen datos de la base de datos actual, entrenan el modelo y lo serializan en `infrastructure/adapters/`. Se pueden re-ejecutar cuando haya más datos disponibles.

---

## 17. Plazo Fijo

### ¿Qué es?

Un plazo fijo es un producto donde el cliente **inmoviliza** un monto de dinero por un período determinado a cambio de un interés fijo.

### Constitución (RF-13)

**Ruta:** `/plazos-fijos/constituir/`

1. El cliente selecciona la cuenta de débito, el monto y el plazo en días (30-365)
2. El sistema muestra una **previsualización en vivo** con el capital, los intereses calculados (8% TNA) y el total al vencimiento
3. Al confirmar, se debita el monto de la cuenta y se crea el plazo fijo

**Cálculo:**
```
interés = capital × 0.08 × días / 365
total_al_vencimiento = capital + interés
```

### Cancelación anticipada (RF-14)

**Ruta:** `/plazos-fijos/<id>/cancelar/` (POST)

Si el cliente cancela antes del vencimiento:

```
días_transcurridos = hoy - fecha_constitución
interés_prorrateado = capital × 0.08 × días_transcurridos / 365
penalización = interés_prorrateado × 50%
devolución = capital + interés_prorrateado - penalización
               = capital + interés_prorrateado × 50%
```

Si se cancela el mismo día, `días_transcurridos = 0`, por lo tanto `interés = 0` y se devuelve solo el capital. Esto evita el exploit de crear y cancelar inmediatamente para ganar intereses.

### Preview con JavaScript

En `static/js/plazofijo_calc.js`, el cálculo se actualiza automáticamente mientras el usuario escribe el monto y los días, sin necesidad de recargar la página.

---

## 18. Historial de Movimientos (RF-06)

**Ruta:** `/historial/`

Vista completa de todas las transacciones del cliente con:

- **Paginación:** 25 transacciones por página
- **Filtros:** por tipo de operación (transferencia, depósito, préstamo, plazo fijo) y por rango de fechas
- **Orden:** del más reciente al más antiguo
- **Indicador de signo:** las transacciones donde el cliente es el origen se muestran en rojo (dinero que sale), las que son destino en verde (dinero que entra)

Implementado con `HistorialView(LoginRequiredMixin, ListView)` y paginación nativa de Django.

---

## 19. Débito Automático de Cuotas

### Campo en el modelo

```python
# infrastructure/models.py
class Prestamo(models.Model):
    ...
    debito_automatico = models.BooleanField(default=False)
```

Al solicitar un préstamo, el cliente puede marcar "Débito automático" (activado por defecto). Si está activo, las cuotas se pagan solas al vencimiento sin intervención del cliente.

### ¿Por qué un Management Command y no una tarea programada (cron/Celery)?

Django tiene un sistema llamado **Management Commands**: archivos Python dentro de `app/management/commands/` que se ejecutan con `python manage.py <nombre>`. Django los descubre automáticamente —no hay que registrarlos en ningún lado—.

Elegimos esta opción por simplicidad académica. Alternativas más complejas serían:
- **Celery:** requiere Redis/RabbitMQ, workers, colas. Sobredimensionado para este proyecto.
- **Cron/Linux:** depende del sistema operativo. Windows tiene Task Scheduler pero es distinto.

El Management Command se puede llamar manualmente o desde cualquier programador de tareas (Task Scheduler, cron, systemd timer). Es la opción más portable y fácil de entender.

### ¿Dónde está el archivo?

```
infrastructure/
├── management/
│   └── commands/
│       └── pagar_cuotas_vencidas.py    ← Django lo descubre automáticamente
├── models.py
├── auth_views.py
...
```

Django busca carpetas `management/commands/` dentro de cada **app** instalada. Cualquier archivo `.py` que encuentre allí se convierte en un comando ejecutable. El nombre del archivo (sin `.py`) es el nombre del comando.

### ¿Qué hace el comando?

`python manage.py pagar_cuotas_vencidas`

1. Busca todas las cuotas con `estado = 'pendiente'` y `fecha_vencimiento <= hoy` de préstamos que tengan `debito_automatico = True`
2. Para cada cuota, dentro de una transacción atómica:
   - Busca la primera cuenta activa del cliente
   - Verifica saldo suficiente
   - Si tiene saldo: debita usando `F('saldo') - monto` (atómico), marca la cuota como pagada, registra la transacción
   - Si no tiene saldo: reporta el error y continúa con la siguiente
3. Al final muestra un resumen de cuántas se pagaron y cuántas fallaron

### Cómo automatizarlo

En Windows, se puede agregar al **Task Scheduler** para que se ejecute todos los días a una hora fija. El comando a ejecutar sería:

```bash
python C:\ruta\al\proyecto\manage.py pagar_cuotas_vencidas
```

---

## 20. Scripts de generación de datos

El sistema incluye varios scripts para poblar la base de datos con datos de prueba:

| Script | Propósito | Cómo ejecutar |
|---|---|---|
| `scripts/generar_datos.py` | Crea 100 usuarios completos con cuentas, alias, CVU, préstamos y transacciones | `python scripts/generar_datos.py` |
| `scripts/generar_masivo.py` | Crea 500 usuarios + ~6.000 transferencias + préstamos + plazos fijos usando ThreadPoolExecutor | `python scripts/generar_masivo.py` |
| `scripts/registro_masivo_concurrente.py` | Registra 20 usuarios vía HTTP concurrente para probar el endpoint | `python scripts/registro_masivo_concurrente.py` |
| `scripts/entrenar_fraude.py` | Entrena el modelo Isolation Forest para detección de fraude | `python scripts/entrenar_fraude.py` |
| `scripts/entrenar_scoring.py` | Entrena el modelo Random Forest para scoring crediticio | `python scripts/entrenar_scoring.py` |

Los scripts `generar_datos.py` y `generar_masivo.py` dejan un archivo `.txt` con los usuarios creados y sus credenciales para facilitar el acceso.

---

*Documentación generada para el proyecto académico Banco Hexagonal.*  
*Última actualización: Julio 2026*
