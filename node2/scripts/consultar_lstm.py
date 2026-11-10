#!/usr/bin/env python3

import subprocess
import re
import sys

SSH_KEY = "/home/pcmadmin/.ssh/pcm_node1_ed25519"
SERVIDOR = "pcmadmin@192.168.56.11"

COMANDO_REMOTO = (
    "docker run --rm "
    "-v /home/pcmadmin/pcm-lstm:/pcm-lstm:ro "
    "pcm-lstm-real:v1 "
    "python /pcm-lstm/predecir_cpu_real.py"
)

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
        timeout=90,
        check=True
    )

    coincidencia = re.search(
        r"CPU predicha:\s*([-+]?\d+(?:\.\d+)?)%",
        resultado.stdout
    )

    if not coincidencia:
        raise RuntimeError(
            "No se encontro la prediccion en la respuesta:\n"
            + resultado.stdout
        )

    return float(coincidencia.group(1))


def main():
    print("=== CONSULTA REMOTA LSTM V4 ===")

    try:
        prediccion = obtener_prediccion()

        print("Nodo de inferencia: PCM-Node1")
        print("CPU predicha: {:.3f}%".format(prediccion))
        print("Consulta completada correctamente")

        return 0

    except Exception as error:
        print("ERROR:", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
