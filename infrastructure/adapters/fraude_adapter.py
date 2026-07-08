import os
import pickle
import numpy as np
from django.utils import timezone
from datetime import timedelta

modelo = None
scaler = None

MODELO_PATH = os.path.join(os.path.dirname(__file__), 'modelo_fraude.pkl')
SCALER_PATH = MODELO_PATH.replace('.pkl', '_scaler.pkl')


def _cargar():
    global modelo, scaler
    if modelo is None:
        with open(MODELO_PATH, 'rb') as f:
            modelo = pickle.load(f)
        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)


def evaluar_transferencia(monto, cuenta_origen_id):
    """
    Evalúa una transferencia y retorna score de riesgo 0.0 a 1.0.
    0.0 = normal, 1.0 = fraude probable.
    """
    _cargar()

    from infrastructure.models import Transaccion, Cuenta
    ahora = timezone.now()
    hace_24h = ahora - timedelta(hours=24)

    cantidad_24h = Transaccion.objects.filter(
        cuenta_origen_id=cuenta_origen_id,
        fecha_creacion__gte=hace_24h,
    ).count()

    cta = Cuenta.objects.filter(id=cuenta_origen_id).first()
    saldo_origen = float(cta.saldo) if cta else 0.0
    hora = ahora.hour
    dia_semana = ahora.weekday()

    features = np.array([[float(monto), hora, dia_semana, float(saldo_origen)]])

    score = modelo.decision_function(features)[0]
    score_min = scaler['score_min']
    score_max = scaler['score_max']
    risk = 1.0 - (score - score_min) / (score_max - score_min + 1e-10)
    risk = max(0.0, min(1.0, risk))

    return round(risk, 4)
