#!/usr/bin/env python3

import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "pcm-orquestador"
DESTINO = BASE / "comparacion_v5/growth_predictivo"
DESTINO.mkdir(parents=True, exist_ok=True)

print("=== GROWTH PREDICTIVO LSTM V5 ===", flush=True)

with (DESTINO / "growth.log").open("w") as log_growth, \
     (DESTINO / "controlador.log").open("w") as log_control:
    growth = subprocess.Popen(
        [sys.executable, str(BASE / "scripts/experimento_growth_v5_nuevo.py")],
        stdout=log_growth,
        stderr=subprocess.STDOUT
    )

    print("Generador Growth iniciado.", flush=True)

    time.sleep(65)

    print("Ejecutando LSTM V5...", flush=True)

    controlador = subprocess.run(
        [
            sys.executable,
            str(BASE / "scripts/controlador_pcm_v5.py"),
            "--autorizar-conmutacion"
        ],
        stdout=log_control,
        stderr=subprocess.STDOUT
    )

    growth.wait()

print("Resultado controlador:", controlador.returncode)
print("Resultado Growth:", growth.returncode)
print("Registros:", DESTINO)
print("=== EXPERIMENTO FINALIZADO ===")
