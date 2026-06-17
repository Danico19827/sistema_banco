from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from math import ceil
from typing import List


def validar_saldo_suficiente(saldo: Decimal, monto: Decimal) -> bool:
    return saldo >= monto > 0


def validar_mismo_cliente(cuenta_origen_id: int, cuenta_destino_id: int) -> bool:
    return cuenta_origen_id != cuenta_destino_id


def validar_monto_positivo(monto: Decimal) -> bool:
    return monto > 0


@dataclass
class CuotaSimulada:
    numero: int
    monto_cuota: Decimal
    interes: Decimal
    amortizacion: Decimal
    saldo_pendiente: Decimal


def simular_cuotas_frances(
    monto: Decimal,
    tasa_anual: float,
    plazo_meses: int,
) -> List[CuotaSimulada]:
    saldo = monto
    tasa_mensual = Decimal(str(tasa_anual / 12))
    cuota_fija = monto * tasa_mensual * (1 + tasa_mensual) ** plazo_meses / ((1 + tasa_mensual) ** plazo_meses - 1)
    cuotas: List[CuotaSimulada] = []

    for i in range(1, plazo_meses + 1):
        interes = saldo * tasa_mensual
        amortizacion = cuota_fija - interes
        saldo -= amortizacion
        if i == plazo_meses:
            saldo = Decimal('0.00')
        cuotas.append(CuotaSimulada(
            numero=i,
            monto_cuota=cuota_fija,
            interes=interes,
            amortizacion=amortizacion,
            saldo_pendiente=saldo,
        ))

    return cuotas


def simular_cuotas_aleman(
    monto: Decimal,
    tasa_anual: float,
    plazo_meses: int,
) -> List[CuotaSimulada]:
    saldo = monto
    tasa_mensual = Decimal(str(tasa_anual / 12))
    amortizacion_fija = monto / plazo_meses
    cuotas: List[CuotaSimulada] = []

    for i in range(1, plazo_meses + 1):
        interes = saldo * tasa_mensual
        saldo -= amortizacion_fija
        if i == plazo_meses:
            saldo = Decimal('0.00')
        cuotas.append(CuotaSimulada(
            numero=i,
            monto_cuota=amortizacion_fija + interes,
            interes=interes,
            amortizacion=amortizacion_fija,
            saldo_pendiente=saldo,
        ))

    return cuotas


def calcular_score_crediticio(
    ingreso_mensual: Decimal,
    score_inicial: int,
    antiguedad_meses: int,
    tiene_ingreso: bool,
) -> float:
    base = score_inicial / 1000.0  # normalizar a 0-1
    if tiene_ingreso:
        ingreso_peso = min(float(ingreso_mensual) / 1_000_000, 1.0)
        base = base * 0.7 + ingreso_peso * 0.3
    base = base * (1 - min(antiguedad_meses / 120, 0.5))
    return max(0.0, min(base, 1.0))
