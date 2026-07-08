"""
Entrena un modelo Isolation Forest para detección de fraude.
Usa las transacciones existentes como datos "normales" y genera
algunas anómalas sintéticas para validación.
"""
import os
import sys
import random
import pickle
from datetime import datetime, timedelta
from decimal import Decimal

import django
import numpy as np
from sklearn.ensemble import IsolationForest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from infrastructure.models import Transaccion, Cuenta


MODELO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'infrastructure', 'adapters', 'modelo_fraude.pkl'
)


def extraer_caracteristicas():
    """Extrae features de las transacciones existentes."""
    transactions = list(Transaccion.objects.filter(
        tipo='transferencia', estado='completada'
    ).select_related('cuenta_origen'))

    if not transactions:
        print('No hay transacciones para entrenar.')
        return [], []

    features = []
    for tx in transactions:
        hora = tx.fecha_creacion.hour
        dia_semana = tx.fecha_creacion.weekday()
        monto = float(tx.monto)
        saldo_origen = float(tx.cuenta_origen.saldo) if tx.cuenta_origen else 0

        features.append([monto, hora, dia_semana, saldo_origen])

    return np.array(features), transactions


def generar_anomalias(cantidad=100):
    """Genera transacciones anómalas sintéticas para validación."""
    anomalias = []
    for _ in range(cantidad):
        monto = random.uniform(50000, 500000)  # montos muy altos
        hora = random.choice([2, 3, 4, 5])  # madrugada
        dia_semana = random.randint(0, 6)
        saldo_origen = random.uniform(10000, 100000)  # saldo bajo vs monto alto
        anomalias.append([monto, hora, dia_semana, saldo_origen])
    return np.array(anomalias)


def main():
    print('Extrayendo características de transacciones normales...')
    X_normales, txs = extraer_caracteristicas()
    print(f'  {len(X_normales)} transacciones normales encontradas')

    if len(X_normales) < 50:
        print('Muy pocas transacciones para entrenar. Generando datos sintéticos...')
        return

    X_anomalias = generar_anomalias(100)
    print(f'  {len(X_anomalias)} anomalías sintéticas generadas para validación')

    X_entreno = X_normales
    X_validacion = np.vstack([X_normales[:50], X_anomalias])
    y_validacion = np.array([0]*50 + [1]*100)

    print('Entrenando Isolation Forest...')
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_entreno)

    # Evaluación
    scores = model.decision_function(X_validacion)
    predictions = model.predict(X_validacion)
    predictions = np.where(predictions == -1, 1, 0)  # -1 = anomalía → 1

    # Normalizar scores a 0-1 (más alto = más anómalo)
    scores_norm = 1 - (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)

    from sklearn.metrics import accuracy_score, precision_score, recall_score
    acc = accuracy_score(y_validacion, predictions)
    prec = precision_score(y_validacion, predictions)
    rec = recall_score(y_validacion, predictions)
    print(f'  Accuracy: {acc:.3f}')
    print(f'  Precision: {prec:.3f}')
    print(f'  Recall: {rec:.3f}')

    # Guardar modelo
    with open(MODELO_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f'Modelo guardado en: {MODELO_PATH}')

    # Guardar stats de normalización desde datos normales
    scores_normales = model.decision_function(X_entreno)
    scaler_path = MODELO_PATH.replace('.pkl', '_scaler.pkl')
    with open(scaler_path, 'wb') as f:
        pickle.dump({
            'score_min': float(scores_normales.min()),
            'score_max': float(scores_normales.max()),
        }, f)
    print(f'Stats de normalización guardados en: {scaler_path}')
    print(f'  Score min (normal): {scores_normales.min():.4f}')
    print(f'  Score max (normal): {scores_normales.max():.4f}')


if __name__ == '__main__':
    main()
