from django.contrib import admin
from .models import (
    Cliente,
    ConfiguracionSeguridad,
    Cuenta,
    Tarjeta,
    Prestamo,
    CuotaPrestamo,
    Transaccion,
    AlertaFraude
)

# Registramos todos los modelos para que el Administrador tenga control total
admin.site.register(Cliente)
admin.site.register(ConfiguracionSeguridad)
admin.site.register(Cuenta)
admin.site.register(Tarjeta)
admin.site.register(Prestamo)
admin.site.register(CuotaPrestamo)
admin.site.register(Transaccion)
admin.site.register(AlertaFraude)