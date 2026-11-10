#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

ARCHIVO_LOCAL = Path(
    "/home/pcmadmin/pcm-orquestador/metricas/cpu_tiempo_real.csv"
)

DESTINO = (
    "pcmadmin@192.168.56.11:"
    "/home/pcmadmin/pcm-lstm/cpu_tiempo_real.csv"
)

SSH_KEY = "/home/pcmadmin/.ssh/pcm_node1_ed25519"


def main():
    print("=== ACTUALIZACION DE METRICAS LSTM ===")

    if not ARCHIVO_LOCAL.is_file():
        print("ERROR: No existe el archivo de metricas")
        return 1

    try:
        subprocess.run(
            [
                "scp",
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=5",
                "-i", SSH_KEY,
                str(ARCHIVO_LOCAL),
                DESTINO
            ],
            check=True,
            timeout=30
        )

        print("Metricas transferidas correctamente")
        print("Origen: PCM-Node2")
        print("Destino: PCM-Node1")
        return 0

    except Exception as error:
        print("ERROR:", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
