#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

BASE = Path.home() / "pcm-orquestador"
SCRIPTS = BASE / "scripts"

def ejecutar(nombre):
    print("\n=== EJECUTANDO {} ===".format(nombre), flush=True)

    resultado = subprocess.run(
        [sys.executable, str(SCRIPTS / nombre)],
        check=False
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            "{} fallo con codigo {}".format(
                nombre, resultado.returncode
            )
        )

print("=== CICLO PCM V5 ===", flush=True)

ejecutar("recolectar_cpu_cgroup.py")

origen = BASE / "metricas/cpu_cgroup_carga.csv"

subprocess.run([
    "scp",
    "-i", str(Path.home() / ".ssh/pcm_node1_ed25519"),
    str(origen),
    "pcmadmin@192.168.56.11:/home/pcmadmin/pcm-lstm/cpu_tiempo_real.csv"
], check=True)

print("Metricas actualizadas correctamente", flush=True)

ejecutar("evaluar_lstm_v5.py")

print("\nCICLO PCM V5 FINALIZADO")
print("MODO SEGURO: SIN MIGRACION AUTOMATICA")
