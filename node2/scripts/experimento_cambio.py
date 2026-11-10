#!/usr/bin/env python3

import subprocess
import time
import sys
import shutil
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "pcm-orquestador"
SCRIPTS = BASE / "scripts"
RESULTADOS = BASE / "resultados"

RESULTADOS.mkdir(parents=True, exist_ok=True)

print("=== EXPERIMENTO PCM: CAMBIO DE TRAFICO ===", flush=True)

monitor = subprocess.Popen([
    sys.executable,
    str(SCRIPTS / "monitor_disponibilidad.py")
])

try:
    print("Monitor iniciado. Esperando 5 segundos...", flush=True)
    time.sleep(5)

    if monitor.poll() is not None:
        raise RuntimeError("El monitor termino antes del cambio")

    print("\n=== CAMBIANDO TRAFICO A PCM-NODE3 ===", flush=True)

    cambio = subprocess.run([
        sys.executable,
        str(SCRIPTS / "cambiar_trafico.py"),
        "node3"
    ])

    print("Codigo de salida del cambio:", cambio.returncode, flush=True)

    monitor.wait(timeout=30)

    origen = RESULTADOS / "monitor_disponibilidad.csv"
    destino = RESULTADOS / (
        "experimento_cambio_" +
        datetime.now().strftime("%Y%m%d_%H%M%S") +
        ".csv"
    )

    shutil.copy2(origen, destino)

    print("\n=== EXPERIMENTO FINALIZADO ===")
    print("Resultados guardados en:", destino)

    if cambio.returncode != 0:
        print("ADVERTENCIA: El cambio de trafico fallo")
        sys.exit(1)

except Exception as error:
    print("ERROR:", error)
    if monitor.poll() is None:
        monitor.terminate()
        try:
            monitor.wait(timeout=5)
        except subprocess.TimeoutExpired:
            monitor.kill()
            monitor.wait()
    sys.exit(1)
