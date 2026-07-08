import os
import pickle
import numpy as np
from datetime import date

modelo = None
MODELO_PATH = os.path.join(os.path.dirname(__file__), 'modelo_scoring.pkl')

MAP_EDUCACION = {
    'primario': 1, 'secundario': 2,
    'terciario': 3, 'universitario': 4, 'posgrado': 5,
}


def _cargar():
    global modelo
    if modelo is None:
        with open(MODELO_PATH, 'rb') as f:
            modelo = pickle.load(f)


def evaluar_cliente(cliente_id):
    """Retorna score de riesgo crediticio 0.0 (bajo) a 1.0 (alto)."""
    _cargar()

    from infrastructure.models import Cliente, CuotaPrestamo
    from django.db.models import Count

    try:
        c = Cliente.objects.annotate(
            cant_prestamos=Count('prestamos'),
        ).get(id=cliente_id)
    except Cliente.DoesNotExist:
        return 0.5

    hoy = date.today()
    edad = hoy.year - c.fecha_nacimiento.year if c.fecha_nacimiento else 30
    ingreso = float(c.ingreso_mensual or 0)
    educ = MAP_EDUCACION.get(c.nivel_educativo, 0)
    score = c.score_crediticio_inicial
    antiguedad = (hoy - c.fecha_registro.date()).days
    cant_prestamos = c.cant_prestamos
    genero_m = 1 if c.genero == 'M' else 0
    genero_f = 1 if c.genero == 'F' else 0

    features = np.array([[
        edad, ingreso, educ, score, antiguedad,
        cant_prestamos, genero_m, genero_f,
    ]])

    proba = modelo.predict_proba(features)[0]
    # proba[0] = proba de clase 0 (mal pagador)
    # proba[1] = proba de clase 1 (buen pagador)
    riesgo = float(proba[0])

    return round(riesgo, 4)
