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
