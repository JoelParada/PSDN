import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
import tensorflow as tf

BASE = Path("/pcm-lstm/entrenamiento_v5")
DATASET = BASE / "datasets/dataset_maestro_pcm_v5.csv"
RESULTADOS = BASE / "results_v5"

VENTANA = 10

grupos = defaultdict(list)

with DATASET.open(newline="", encoding="utf-8") as archivo:
    for fila in csv.DictReader(archivo):
        grupos[fila["experimento_id"]].append(fila)

pruebas = []

for nombre, filas in grupos.items():
    filas.sort(key=lambda f: f["timestamp"])
    valores = [float(f["cpu_pct"]) for f in filas]

    if len(valores) <= VENTANA + 2:
        continue

    corte = max(VENTANA + 1, int(len(valores) * 0.8))

    for i in range(VENTANA, len(valores)):
        if i >= corte:
            pruebas.append({
                "experimento_id": nombre,
                "timestamp": filas[i]["timestamp"],
                "ventana": valores[i-VENTANA:i],
                "cpu_real": valores[i]
            })

parametros = np.load(
    RESULTADOS / "parametros_normalizacion_pcm_v5.npz"
)

minimo = float(parametros["minimo"])
rango = float(parametros["rango"])

X = np.array([
    [(v - minimo) / rango for v in fila["ventana"]]
    for fila in pruebas
], dtype=np.float32).reshape(-1, VENTANA, 1)

modelo = tf.keras.models.load_model(
    RESULTADOS / "cpu_forecaster_pcm_v5.keras",
    compile=False
)

predicciones = modelo.predict(X, verbose=0).reshape(-1)
predicciones = predicciones * rango + minimo

salida = RESULTADOS / "predicciones_vs_reales_v5.csv"

with salida.open("w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo)

    escritor.writerow([
        "experimento_id",
        "timestamp",
        "cpu_real",
        "cpu_predicha",
        "error_absoluto"
    ])

    for fila, prediccion in zip(pruebas, predicciones):
        real = fila["cpu_real"]

        escritor.writerow([
            fila["experimento_id"],
            fila["timestamp"],
            real,
            float(prediccion),
            abs(real - float(prediccion))
        ])

reales = np.array([fila["cpu_real"] for fila in pruebas])
mae = np.mean(np.abs(reales - predicciones))
rmse = np.sqrt(np.mean((reales - predicciones) ** 2))

print("=== EVALUACION LSTM V5 ===")
print("Secuencias de prueba:", len(pruebas))
print("MAE: {:.4f}".format(mae))
print("RMSE: {:.4f}".format(rmse))
print("CSV generado:", salida)
