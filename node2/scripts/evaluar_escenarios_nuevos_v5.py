#!/usr/bin/env python3
import subprocess
from pathlib import Path

BASE = Path.home() / "pcm-orquestador"
DATOS = BASE / "experimentos_v5_nuevos/datos"
KEY = str(Path.home() / ".ssh/pcm_node1_ed25519")

archivos = [
    DATOS / "growth_v5_20261110_020233.csv",
    DATOS / "spike_v5_20261110_020639.csv"
]

for archivo in archivos:
    if not archivo.exists():
        raise SystemExit(f"Falta el archivo: {archivo}")

remoto = "/home/pcmadmin/pcm-lstm/evaluacion_nueva_v5"
subprocess.run([
    "ssh", "-i", KEY, "pcmadmin@192.168.56.11",
    f"mkdir -p {remoto}"
], check=True)

for archivo in archivos:
    subprocess.run([
        "scp", "-i", KEY, str(archivo),
        f"pcmadmin@192.168.56.11:{remoto}/"
    ], check=True)

print("CSV REALES COPIADOS A NODE1")
print("Modelo LSTM original: sin modificaciones")
