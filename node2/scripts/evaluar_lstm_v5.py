#!/usr/bin/env python3

import subprocess
import re
from pathlib import Path

from detectar_nodo_activo import obtener_nodo_activo
from evaluar_migracion import decidir_migracion

KEY = str(Path.home() / ".ssh/pcm_node1_ed25519")

COMANDO_REMOTO = """
docker run --rm -i \
-v /home/pcmadmin/pcm-lstm:/pcm-lstm \
pcm-lstm-real:v1 python - <<'REMOTE_PY'
import csv
import numpy as np
import tensorflow as tf

base = '/pcm-lstm/entrenamiento_v5/results_v5/'

with open('/pcm-lstm/cpu_tiempo_real.csv', newline='') as f:
    filas = list(csv.DictReader(f))

valores = np.array(
    [float(f['cpu_percent']) for f in filas[-10:]],
    dtype=np.float32
)

if len(valores) != 10:
    raise ValueError('Se requieren 10 mediciones')

p = np.load(base + 'parametros_normalizacion_pcm_v5.npz')
modelo = tf.keras.models.load_model(
    base + 'cpu_forecaster_pcm_v5.keras'
)

minimo = float(p['minimo'])
rango = float(p['rango'])

X = ((valores - minimo) / rango).reshape(1, 10, 1)
pred = modelo.predict(X, verbose=0)[0][0]

print('CPU_PREDICHA_V5={:.4f}'.format(
    float(pred * rango + minimo)
))
REMOTE_PY
"""

print("=== EVALUACION PCM CON LSTM V5 ===")

resultado = subprocess.run(
    [
        "ssh", "-i", KEY, "-o", "BatchMode=yes",
        "pcmadmin@192.168.56.11", COMANDO_REMOTO
    ],
    capture_output=True,
    text=True,
    timeout=120,
    check=True
)

coincidencia = re.search(
    r"CPU_PREDICHA_V5=([-+]?\d+(?:\.\d+)?)",
    resultado.stdout
)

if not coincidencia:
    raise RuntimeError(resultado.stdout + resultado.stderr)

prediccion = float(coincidencia.group(1))
nodo = obtener_nodo_activo()
decision = decidir_migracion(prediccion, nodo)

print("CPU predicha V5: {:.2f}%".format(prediccion))
print("Nodo activo:", nodo)
print("Decision:", decision)
print("MODO SEGURO: SIN CAMBIAR TRAFICO")
