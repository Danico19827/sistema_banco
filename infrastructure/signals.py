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
