import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import tensorflow as tf

BASE = Path('/pcm-lstm/entrenamiento_v5')
DATASET = BASE / 'datasets/dataset_maestro_pcm_v5.csv'
RESULTADOS = BASE / 'results_v5'
RESULTADOS.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
tf.random.set_seed(42)

VENTANA = 10
UMBRAL = 80.0

grupos = defaultdict(list)

with DATASET.open(newline='') as archivo:
    for fila in csv.DictReader(archivo):
        grupos[fila['experimento_id']].append(fila)

train = []
test = []

for nombre, filas in grupos.items():
    filas.sort(key=lambda x: x['timestamp'])
    valores = [float(f['cpu_pct']) for f in filas]

    if len(valores) <= VENTANA + 2:
        continue

    corte = max(VENTANA + 1, int(len(valores) * 0.8))

    for i in range(VENTANA, len(valores)):
        ejemplo = (valores[i-VENTANA:i], valores[i])

        if i < corte:
            train.append(ejemplo)
        else:
            test.append(ejemplo)

if not train or not test:
    raise RuntimeError('No hay suficientes secuencias de entrenamiento y prueba')

minimo = min(min(x[0]) for x in train)
maximo = max(max(max(x[0]), x[1]) for x in train)
rango = max(maximo - minimo, 1e-8)

def preparar(datos):
    X = np.array(
        [[(v-minimo)/rango for v in ventana] for ventana, _ in datos],
        dtype=np.float32
    ).reshape(-1, VENTANA, 1)
    y = np.array(
        [(objetivo-minimo)/rango for _, objetivo in datos],
        dtype=np.float32
    )
    return X, y

X_train, y_train = preparar(train)
X_test, y_test = preparar(test)

modelo = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(VENTANA, 1)),
    tf.keras.layers.LSTM(32),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1)
])

modelo.compile(optimizer='adam', loss='mse')

modelo.fit(
    X_train, y_train,
    epochs=30,
    batch_size=16,
    verbose=0,
    shuffle=False
)

pred_norm = modelo.predict(X_test, verbose=0).reshape(-1)
pred = pred_norm * rango + minimo
real = y_test * rango + minimo

mae = float(np.mean(np.abs(pred-real)))
rmse = float(np.sqrt(np.mean((pred-real)**2)))

persistencia = np.array([v[-1] for v, _ in test])
mae_base = float(np.mean(np.abs(persistencia-real)))

modelo.save(RESULTADOS / 'cpu_forecaster_pcm_v5.keras')

np.savez(
    RESULTADOS / 'parametros_normalizacion_pcm_v5.npz',
    minimo=minimo,
    maximo=maximo,
    rango=rango,
    ventana=VENTANA,
    umbral=UMBRAL
)

resumen = {
    'secuencias_entrenamiento': len(train),
    'secuencias_prueba': len(test),
    'mae_lstm': mae,
    'rmse_lstm': rmse,
    'mae_persistencia': mae_base,
    'umbral_operativo': UMBRAL
}

(RESULTADOS / 'metricas_v5.json').write_text(
    json.dumps(resumen, indent=2)
)

print('=== RESULTADOS LSTM V5 ===')
print(json.dumps(resumen, indent=2))
print('ENTRENAMIENTO FINALIZADO')
