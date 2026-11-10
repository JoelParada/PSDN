#!/usr/bin/env python3

import subprocess
import re
import sys
from pathlib import Path

SSH_KEY = str(Path.home() / ".ssh/pcm_node1_ed25519")
SERVIDOR = "pcmadmin@192.168.56.11"

COMANDO_REMOTO = """
docker run --rm -i \
-v /home/pcmadmin/pcm-lstm:/pcm-lstm:ro \
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

def obtener_prediccion():
    resultado = subprocess.run(
        [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            "-i", SSH_KEY,
            SERVIDOR,
            COMANDO_REMOTO
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
        raise RuntimeError(
            "No se encontro la prediccion V5:\n"
            + resultado.stdout
            + resultado.stderr
        )

    return float(coincidencia.group(1))


def main():
    print("=== CONSULTA REMOTA LSTM V5 ===")

    try:
        prediccion = obtener_prediccion()

        print("Nodo de inferencia: PCM-Node1")
        print("CPU predicha V5: {:.3f}%".format(prediccion))
        print("Consulta completada correctamente")

        return 0

    except Exception as error:
        print("ERROR:", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
