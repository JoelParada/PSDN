#!/usr/bin/env python3

import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "pcm-orquestador"
KEY = str(Path.home() / ".ssh/pcm_node1_ed25519")
HOST = "pcmadmin@192.168.56.11"

monitor = None

try:
    print("=== EXPERIMENTO GROWTH V5 ===", flush=True)

    monitor = subprocess.Popen([
        sys.executable,
        str(BASE / "scripts/recolectar_cpu_ram_v5_nuevos.py"),
        "--escenario", "growth",
        "--muestras", "16",
        "--intervalo", "5"
    ])

    time.sleep(3)

    for etapa, trabajadores in enumerate([1, 2, 3, 4], 1):
        print(
            f"ETAPA {etapa}/4: "
            f"{trabajadores} trabajadores durante 30 segundos",
            flush=True
        )

        comando = f"""
        timeout 30 bash -c '
        for n in $(seq 1 {trabajadores}); do
            (
                while true; do
                    curl -fsS --max-time 10 -o /dev/null \
                    "http://127.0.0.1:5000/compute?iterations=8000000" \
                    || true
                done
            ) &
        done
        wait
        '
        """

        subprocess.run([
            "ssh", "-i", KEY,
            "-o", "BatchMode=yes",
            HOST, comando
        ] , timeout=45, check=False)

    print("Carga Growth finalizada.", flush=True)

    monitor.wait(timeout=180)

    if monitor.returncode != 0:
        raise RuntimeError("El monitor termino con error")

    print("=== GROWTH V5 FINALIZADO ===", flush=True)

finally:
    if monitor and monitor.poll() is None:
        monitor.terminate()
        monitor.wait()
