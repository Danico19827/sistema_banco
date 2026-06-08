from django.db import models
from django.contrib.auth.models import User

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

    #atributos clave para la minerá de datos
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO, default='N')
    profesion = models.CharField(max_length=100, blank=True, verbose_name="Ocupación/Profesión")
    ingreso_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    nivel_educativo = models.CharField(max_length=20, choices=NIVEL_EDUCATIVO, default='secundario')
    score_crediticio_inicial = models.IntegerField(default=500, help_text="Score externo de riesgo al registrarse")

    class Meta:
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name} (DNI: {self.dni})"
    
class ConfiguracionSeguridad(models.Model):
    # Relación 1 a 1 con el Cliente
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='configuracion_seguridad')
    
    intentos_fallidos_login = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    doble_factor_activo = models.BooleanField(default=False)
    #limite_transferencia_diario = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)

    def __str__(self):
        return f"Configuración Seguridad de {self.cliente.usuario.username}"
    
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

class Tarjeta(models.Model):
    TIPO_TARJETA = [
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    ]
    ESTADO_TARJETA = [
        ('activa', 'Activa'),
        ('bloqueada', 'Bloqueada'),
        ('vencida', 'Vencida'),
    ]

    # Relación 1 a Muchos con Cuenta
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='tarjetas')
    
    tipo_tarjeta = models.CharField(max_length=20, choices=TIPO_TARJETA)
    numero = models.CharField(max_length=16, unique=True)
    cvv = models.CharField(max_length=4)  # El código de seguridad detrás
    fecha_expiracion = models.DateField()
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Por si es de crédito
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, choices=ESTADO_TARJETA, default='activa')

    def __str__(self):
        # Muestra el tipo y los últimos 4 dígitos para que sea legible y seguro
        unmasked_digits = self.numero[-4:] if len(self.numero) >= 4 else ''
        return f"Tarjeta {self.tipo_tarjeta.capitalize()} ****{unmasked_digits} - Cuenta {self.cuenta.id}"

class Prestamo(models.Model):
    ESTADO_PRESTAMO = [('activo', 'Activo'), ('pagado', 'Pagado'), ('vencido', 'Vencida/Mora')]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='prestamos')
    monto_original = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_interes_anual = models.FloatField()
    plazo_meses = models.IntegerField()
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PRESTAMO, default='activo')

    def __str__(self):
        return f"Préstamo {self.id} - {self.cliente.usuario.username} - Pendiente: {self.saldo_pendiente}"

class CuotaPrestamo(models.Model):
    ESTADO_CUOTA = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
    ]

    prestamo = models.ForeignKey(
        Prestamo, 
        on_delete=models.CASCADE,  
        related_name='cuotas'
    )
    
    numero_cuota = models.IntegerField()
    monto_cuota = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CUOTA, default='pendiente')

    def __str__(self):
        return f"Préstamo {self.prestamo.id} - Cuota {self.numero_cuota} ({self.estado})"

class Transaccion(models.Model):
    TIPO_TRANSACCION = [
        ('transferencia', 'Transferencia'),
        ('deposito', 'Depósito'),
        ('retiro', 'Retiro'),
        ('pago_tarjeta', 'Pago con Tarjeta'),
        ('pago_prestamo', 'Pago de Préstamo'),
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

class AlertaFraude(models.Model):
    ACCIONES_SISTEMA = [
        ('ninguna', 'Ninguna / En revisión'),
        ('bloqueo_cuenta', 'Bloqueo de Cuenta'),
        ('notificacion_cliente', 'Notificación Enviada'),
        ('transaccion_rechazada', 'Transacción Rechazada'),
    ]

    # Relación 1 a 1
    transaccion = models.OneToOneField(
        Transaccion, 
        on_delete=models.CASCADE, 
        related_name='alerta'
    )
    
    score_riesgo = models.FloatField()  # nivel de peligro
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    accion_tomada = models.CharField(max_length=50, choices=ACCIONES_SISTEMA, default='ninguna')
    resuelta = models.BooleanField(default=False)

    def __str__(self):
        estado_resolucion = "Resuelta" if self.resuelta else "Pendiente"
        return f"Alerta {self.id} - Transacción {self.transaccion.id} ({estado_resolucion})"
    
