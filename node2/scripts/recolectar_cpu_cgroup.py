#!/usr/bin/env python3

import csv
import subprocess
import time
from datetime import datetime
from pathlib import Path

IP = "192.168.56.11"
KEY = str(Path.home() / ".ssh/pcm_node1_ed25519")
DESTINO = Path.home() / "pcm-orquestador/metricas/cpu_cgroup_carga.csv"

COMANDO = (
    "docker exec pcm-flask-app "
    "cat /sys/fs/cgroup/cpuacct/cpuacct.usage"
)

def leer_cpu():
    resultado = subprocess.run(
        ["ssh", "-i", KEY, "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=5", f"pcmadmin@{IP}", COMANDO],
        capture_output=True,
        text=True,
        timeout=12,
        check=True
    )
    return int(resultado.stdout.strip())

def main():
    DESTINO.parent.mkdir(parents=True, exist_ok=True)

    print("=== RECOLECCION CPU CGROUP ===", flush=True)

    with DESTINO.open("w", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["timestamp", "cpu_percent"])

        anterior_cpu = leer_cpu()
        anterior_tiempo = time.monotonic_ns()

        for i in range(10):
            time.sleep(5)

            actual_cpu = leer_cpu()
            actual_tiempo = time.monotonic_ns()

            cpu = 100 * (
                (actual_cpu - anterior_cpu) /
                (actual_tiempo - anterior_tiempo)
            )

            cpu = max(0.0, cpu)

            escritor.writerow([
                datetime.now().isoformat(timespec="seconds"),
                round(cpu, 4)
            ])

            archivo.flush()

            print(
                "Medicion {}/10: {:.2f}%".format(i + 1, cpu),
                flush=True
            )

            anterior_cpu = actual_cpu
            anterior_tiempo = actual_tiempo

    print("Archivo:", DESTINO)
    print("RECOLECCION FINALIZADA")

if __name__ == "__main__":
    main()
