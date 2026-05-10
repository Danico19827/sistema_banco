from django.db import models
from django.contrib.auth.models import User

class Cliente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='activo')

    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"

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

    def __str__(self):
        return f"Cuenta {self.id} - {self.cliente.usuario.username}"

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

    tipo = models.CharField(max_length=20, choices=TIPO_TRANSACCION)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    cuenta_origen = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='transacciones_origen', null=True, blank=True)
    cuenta_destino = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='transacciones_destino', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_TRANSACCION, default='completada')
    descripcion = models.TextField(blank=True)
    riesgo_fraude = models.FloatField(default=0.0)
    es_fraude_confirmado = models.BooleanField(default=False)

    def __str__(self):
        return f"Transacción {self.id} - {self.tipo} - {self.monto}"