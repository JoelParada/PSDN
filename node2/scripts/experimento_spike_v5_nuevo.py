#!/usr/bin/env python3

import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "pcm-orquestador"
KEY = str(Path.home() / ".ssh/pcm_node1_ed25519")
HOST = "pcmadmin@192.168.56.11"

monitor = None

def rafaga(numero):
    print(f"RAFAGA {numero}/4: 25 segundos", flush=True)

    comando = """
    timeout 25 bash -c '
    for n in 1 2 3 4; do
        (
            while true; do
                curl -fsS --max-time 15 -o /dev/null \
                "http://127.0.0.1:5000/compute?iterations=8000000" \
                || true
            done
        ) &
    done
    wait
    '
    """

    resultado = subprocess.run(
        [
            "ssh", "-i", KEY,
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            HOST, comando
        ],
        timeout=40
    )

    if resultado.returncode not in (0, 124):
        raise RuntimeError(
            f"Error en rafaga {numero}: {resultado.returncode}"
        )

try:
    print("=== EXPERIMENTO SPIKE V5 ===", flush=True)

    monitor = subprocess.Popen([
        sys.executable,
        str(BASE / "scripts/recolectar_cpu_ram_v5_nuevos.py"),
        "--escenario", "spike",
        "--muestras", "19",
        "--intervalo", "5"
    ])

    print("REPOSO INICIAL: 15 segundos", flush=True)
    time.sleep(15)

    for numero in range(1, 5):
        rafaga(numero)

        if numero < 4:
            print("REPOSO: 15 segundos", flush=True)
            time.sleep(15)

    print("Carga Spike finalizada.", flush=True)

    monitor.wait(timeout=180)

    if monitor.returncode != 0:
        raise RuntimeError("El monitor termino con error")

    print("=== SPIKE V5 FINALIZADO ===", flush=True)

finally:
    if monitor and monitor.poll() is None:
        monitor.terminate()
        monitor.wait()
