#!/usr/bin/env python3

import csv
import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "pcm-orquestador"
SALIDA = BASE / "metricas" / "cpu_tiempo_real.csv"

SSH_KEY = Path.home() / ".ssh/pcm_node1_ed25519"
SERVIDOR = "pcmadmin@192.168.56.11"
CONTENEDOR = "pcm-flask-app"

TOTAL_MUESTRAS = 10
INTERVALO = 2

SALIDA.parent.mkdir(parents=True, exist_ok=True)

print("=== RECOLECCION CPU EN TIEMPO REAL ===", flush=True)
print("Nodo: PCM-Node1", flush=True)
print("Contenedor:", CONTENEDOR, flush=True)
print("Muestras:", TOTAL_MUESTRAS, flush=True)

with open(SALIDA, "w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo)
    escritor.writerow(["timestamp", "cpu_percent"])

    for numero in range(1, TOTAL_MUESTRAS + 1):
        comando = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            "-i", str(SSH_KEY),
            SERVIDOR,
            "docker stats --no-stream "
            "--format '{{.CPUPerc}}' " + CONTENEDOR
        ]

        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=15,
            check=True
        )

        cpu = float(
            resultado.stdout.strip().replace("%", "")
        )

        timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        escritor.writerow([timestamp, cpu])
        archivo.flush()

        print(
            "Muestra {}/{} | CPU: {:.3f}%".format(
                numero, TOTAL_MUESTRAS, cpu
            ),
            flush=True
        )

        if numero < TOTAL_MUESTRAS:
            time.sleep(INTERVALO)

print("\nRECOLECCION FINALIZADA")
print("Archivo:", SALIDA)
