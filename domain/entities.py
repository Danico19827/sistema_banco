from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List


@dataclass
class ClienteEntity:
    id: int
    usuario_id: int
    dni: str
    nombre: str
    apellido: str
    email: str
    telefono: str
    direccion: str

    fecha_nacimiento: Optional[date] = None
    genero: str = 'N'
    profesion: str = ''
    ingreso_mensual: Optional[Decimal] = None
    nivel_educativo: str = 'secundario'
    score_crediticio_inicial: int = 500


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
    limite_transferencia_diario: Decimal = Decimal('1000.00')


@dataclass
class TransaccionEntity:
    id: int
    tipo: str
    monto: Decimal
    cuenta_origen_id: Optional[int]
    cuenta_destino_id: Optional[int]
    descripcion: str = ''
    estado: str = 'completada'
    fecha_creacion: Optional[datetime] = None
    riesgo_fraude: float = 0.0
    es_fraude_confirmado: bool = False


@dataclass
class PrestamoEntity:
    id: int
    cliente_id: int
    monto_original: Decimal
    saldo_pendiente: Decimal
    tasa_interes_anual: float
    plazo_meses: int
    sistema_amortizacion: str = 'frances'
    estado: str = 'activo'
    cuotas: List['CuotaEntity'] = field(default_factory=list)


@dataclass
class CuotaEntity:
    id: int
    prestamo_id: int
    numero_cuota: int
    monto_cuota: Decimal
    fecha_vencimiento: date
    estado: str = 'pendiente'
    fecha_pago: Optional[date] = None
    monto_pagado: Optional[Decimal] = None


@dataclass
class PlazoFijoEntity:
    id: int
    cliente_id: int
    cuenta_id: int
    monto: Decimal
    plazo_dias: int
    tasa_interes_anual: float
    monto_al_vencimiento: Decimal
    fecha_constitucion: Optional[datetime] = None
    fecha_vencimiento: Optional[date] = None
    estado: str = 'activo'
