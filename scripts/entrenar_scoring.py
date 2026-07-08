"""
Entrena un RandomForest para scoring crediticio.
Features: edad, ingreso, nivel educativo, score inicial,
antigüedad de cuenta, morosidad previa, cantidad de préstamos.
"""
import os
import sys
import pickle

import django
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db.models import Count, Q
from infrastructure.models import Cliente, CuotaPrestamo
from datetime import date


MODELO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'infrastructure', 'adapters', 'modelo_scoring.pkl'
)

MAP_EDUCACION = {
    'primario': 1, 'secundario': 2,
    'terciario': 3, 'universitario': 4, 'posgrado': 5,
}


def extraer_features():
    hoy = date.today()
    features, labels = [], []
    ids = []

    clientes = Cliente.objects.filter(
        prestamos__isnull=False
    ).annotate(
        cant_prestamos=Count('prestamos'),
    ).prefetch_related('prestamos__cuotas').distinct()

    for c in clientes:
        if not c.fecha_nacimiento:
            continue

        edad = hoy.year - c.fecha_nacimiento.year
        ingreso = float(c.ingreso_mensual or 0)
        educ = MAP_EDUCACION.get(c.nivel_educativo, 0)
        score = c.score_crediticio_inicial
        antiguedad = (hoy - c.fecha_registro.date()).days
        cant_prestamos = c.cant_prestamos
        genero_m = 1 if c.genero == 'M' else 0
        genero_f = 1 if c.genero == 'F' else 0

        cuotas_vencidas = CuotaPrestamo.objects.filter(
            prestamo__cliente=c, estado='vencida'
        ).count()

        # Label: 1 = buen pagador, 0 = mal pagador
        es_malo = cuotas_vencidas >= 2
        labels.append(0 if es_malo else 1)

        features.append([
            edad, ingreso, educ, score, antiguedad,
            cant_prestamos, genero_m, genero_f,
        ])
        ids.append(c.id)

    return np.array(features), np.array(labels), ids


def main():
    print('Extrayendo features de clientes con préstamos...')
    X, y, ids = extraer_features()
    print(f'  Total muestras: {len(X)}')
    print(f'  Buenos pagadores: {sum(y)}')
    print(f'  Malos pagadores: {sum(y == 0)}')

    if len(X) < 20:
        print('Muy pocos datos para entrenar.')
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200, max_depth=10,
        min_samples_leaf=3, random_state=42,
        class_weight='balanced', n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    print(f'\nResultados en test:')
    print(f'  Accuracy:  {acc:.3f}')
    print(f'  Precision: {prec:.3f}')
    print(f'  Recall:    {rec:.3f}')
    print(f'  F1-score:  {f1:.3f}')

    feature_names = [
        'edad', 'ingreso', 'educacion', 'score_inicial',
        'antiguedad', 'cant_prestamos', 'genero_m', 'genero_f',
    ]
    importances = sorted(zip(feature_names, model.feature_importances_),
                         key=lambda x: -x[1])
    print('\nImportancia de features:')
    for name, imp in importances:
        print(f'  {name}: {imp:.4f}')

    with open(MODELO_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f'\nModelo guardado en: {MODELO_PATH}')


if __name__ == '__main__':
    main()
