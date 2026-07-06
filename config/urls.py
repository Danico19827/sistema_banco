from django.contrib import admin
#from django.contrib.auth import views
from django.urls import path
from django.contrib.auth.views import LogoutView
from infrastructure.auth_views import (
    InicioView, RegistroView, InicioSesionView, PanelView, TransferenciaView,
    PrestamoListView, PrestamoCrearView, PrestamoDetalleView,
    MetricasView
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('metricas/', MetricasView.as_view(), name='metricas'),
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

