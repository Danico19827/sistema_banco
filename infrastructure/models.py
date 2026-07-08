import unicodedata
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

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

    #atributos clave para la minerá de datos
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
    
class ConfiguracionSeguridad(models.Model):
    # Relación 1 a 1 con el Cliente
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='configuracion_seguridad')
    
    intentos_fallidos_login = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    doble_factor_activo = models.BooleanField(default=False)
    #limite_transferencia_diario = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)

    class Meta:
        verbose_name = 'Configuración de seguridad'
        verbose_name_plural = 'Configuraciones de seguridad'

    def __str__(self):
        return f"Configuración Seguridad de {self.cliente.usuario.username}"
    
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
        if not self.alias:
            self.alias = self._generar_alias()
        if not self.cvu:
            self.cvu = self._generar_cvu()
        super().save(*args, **kwargs)

    def _generar_alias(self):
        def limpiar(texto):
            texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
            return ''.join(c for c in texto if c.isalnum()).lower()
        usuario = self.cliente.usuario
        if usuario.first_name and usuario.last_name:
            base = f"{limpiar(usuario.first_name)}.{limpiar(usuario.last_name)}"
        else:
            base = limpiar(usuario.username)
        sufijo = uuid.uuid4().hex[:4]
        alias = f"{base}.{sufijo}"[:20]
        if not alias.endswith(sufijo):
            alias = f"{base[:15]}.{sufijo}"[:20]
        while Cuenta.objects.filter(alias=alias).exists():
            sufijo = uuid.uuid4().hex[:4]
            alias = f"{base[:15]}.{sufijo}"[:20]
        return alias

    def _generar_cvu(self):
        cvu = '0' + str(uuid.uuid4().int % 10**21).zfill(21)
        while Cuenta.objects.filter(cvu=cvu).exists():
            cvu = '0' + str(uuid.uuid4().int % 10**21).zfill(21)
        return cvu

    def __str__(self):
        return f"Cuenta {self.numero_cuenta} - {self.cliente.usuario.username}"

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

    def __str__(self):
        unmasked_digits = self.numero[-4:] if len(self.numero) >= 4 else ''
        return f"Tarjeta {self.tipo_tarjeta.capitalize()} ****{unmasked_digits}"

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
    debito_automatico = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'
        ordering = ['-fecha_inicio']

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
    fecha_pago = models.DateField(null=True, blank=True)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CUOTA, default='pendiente')

    class Meta:
        verbose_name = 'Cuota de préstamo'
        verbose_name_plural = 'Cuotas de préstamo'
        ordering = ['prestamo', 'numero_cuota']

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

    class Meta:
        verbose_name = 'Alerta de fraude'
        verbose_name_plural = 'Alertas de fraude'
        ordering = ['-fecha_alerta']

    def __str__(self):
        estado_resolucion = "Resuelta" if self.resuelta else "Pendiente"
        return f"Alerta {self.id} - Transacción {self.transaccion.id} ({estado_resolucion})"

class PlazoFijo(models.Model):
    ESTADO_PLAZO = [
        ('activo', 'Activo'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='plazos_fijos')
    cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='plazos_fijos')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    plazo_dias = models.IntegerField()
    tasa_interes_anual = models.FloatField()
    fecha_constitucion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    monto_al_vencimiento = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    estado = models.CharField(max_length=20, choices=ESTADO_PLAZO, default='activo')

    class Meta:
        verbose_name = 'Plazo fijo'
        verbose_name_plural = 'Plazos fijos'
        ordering = ['-fecha_constitucion']

    def __str__(self):
        return f"Plazo Fijo {self.id} - {self.cliente.usuario.username} - ${self.monto}"
    
