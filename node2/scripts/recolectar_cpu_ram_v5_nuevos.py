#!/usr/bin/env python3

import argparse
import csv
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "pcm-orquestador/experimentos_v5_nuevos/datos"
KEY = str(Path.home() / ".ssh/pcm_node1_ed25519")
HOST = "pcmadmin@192.168.56.11"

parser = argparse.ArgumentParser()
parser.add_argument("--escenario", required=True, choices=["growth", "spike"])
parser.add_argument("--muestras", type=int, default=40)
parser.add_argument("--intervalo", type=float, default=5)
args = parser.parse_args()

if args.muestras < 1 or args.intervalo <= 0:
    parser.error("Las muestras y el intervalo deben ser positivos")

BASE.mkdir(parents=True, exist_ok=True)

identificador = datetime.now().strftime("%Y%m%d_%H%M%S")
archivo = BASE / f"{args.escenario}_v5_{identificador}.csv"

def ejecutar_remoto(comando):
    resultado = subprocess.run(
        [
            "ssh", "-i", KEY,
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            HOST, comando
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True
    )
    return resultado.stdout.strip()

def leer_cpu():
    return int(ejecutar_remoto(
        "docker exec pcm-flask-app "
        "cat /sys/fs/cgroup/cpuacct/cpuacct.usage"
    ))

def leer_ram():
    salida = ejecutar_remoto(
        "docker stats --no-stream "
        "--format '{{.MemUsage}}' pcm-flask-app"
    )

    usado = salida.split("/")[0].strip()
    coincidencia = re.fullmatch(
        r"([0-9]+(?:[.,][0-9]+)?)\s*([A-Za-z]+)",
        usado
    )

    if not coincidencia:
        raise ValueError(f"Formato RAM no reconocido: {usado}")

    numero, unidad = coincidencia.groups()
    valor = float(numero.replace(",", "."))

    factores = {
        "B": 1 / (1024 * 1024),
        "KiB": 1 / 1024,
        "MiB": 1,
        "GiB": 1024,
        "kB": 1000 / (1024 * 1024),
        "MB": 1000 * 1000 / (1024 * 1024),
        "GB": 1000 * 1000 * 1000 / (1024 * 1024)
    }

    if unidad not in factores:
        raise ValueError(f"Unidad RAM no reconocida: {unidad}")

    return valor * factores[unidad]

print("=== MONITOREO CPU/RAM PCM V5 ===", flush=True)
print("Escenario:", args.escenario, flush=True)
print("Muestras:", args.muestras, flush=True)
print("Archivo:", archivo, flush=True)

with archivo.open("w", newline="", encoding="utf-8") as f:
    escritor = csv.writer(f)
    escritor.writerow([
        "timestamp",
        "experimento_id",
        "escenario",
        "nodo",
        "cpu_pct",
        "ram_mib",
        "segundos_desde_inicio"
    ])

    anterior_cpu = leer_cpu()
    anterior_tiempo = time.monotonic_ns()
    inicio = time.monotonic()

    for i in range(args.muestras):
        time.sleep(args.intervalo)

        actual_cpu = leer_cpu()
        actual_tiempo = time.monotonic_ns()

        cpu = 100 * (
            (actual_cpu - anterior_cpu) /
            (actual_tiempo - anterior_tiempo)
        )
        cpu = max(0.0, cpu)

        ram = leer_ram()

        escritor.writerow([
            datetime.now().isoformat(timespec="seconds"),
            f"{args.escenario}_v5_{identificador}",
            args.escenario,
            "pcm-node1",
            round(cpu, 4),
            round(ram, 4),
            round(time.monotonic() - inicio, 2)
        ])
        f.flush()

        print(
            f"Muestra {i+1}/{args.muestras}: "
            f"CPU={cpu:.2f}% | RAM={ram:.2f} MiB",
            flush=True
        )

        anterior_cpu = actual_cpu
        anterior_tiempo = actual_tiempo

print("MONITOREO FINALIZADO", flush=True)
print("CSV:", archivo, flush=True)
