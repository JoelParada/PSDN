#!/usr/bin/env python3

import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "pcm-orquestador"
SCRIPTS = BASE / "scripts"
RESULTADOS = BASE / "resultados"
RESULTADOS.mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--autorizar-conmutacion", action="store_true")
args = parser.parse_args()

fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
log = RESULTADOS / ("integral_v5_" + fecha + ".log")

monitor = None
carga = None

def detener(proceso):
    if proceso and proceso.poll() is None:
        proceso.terminate()
        try:
            proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait()

try:
    print("=== PRUEBA INTEGRAL PCM V5 ===", flush=True)

    from detectar_nodo_activo import obtener_nodo_activo

    if obtener_nodo_activo() != "pcm-node1":
        raise RuntimeError("PCM-Node1 debe estar activo")

    # Genera solicitudes de computo durante 120 segundos.
    carga = subprocess.Popen([
        "ssh",
        "-i", str(Path.home() / ".ssh/pcm_node1_ed25519"),
        "pcmadmin@192.168.56.11",
        "timeout 120 bash -c '"
        "for n in 1 2; do "
        "(while true; do "
        "curl -fsS -o /dev/null "
        "\"http://127.0.0.1:5000/compute?iterations=2000000\" "
        "|| break; done) & "
        "done; wait'"
    ], stdout=subprocess.DEVNULL)

    print("Carga iniciada en PCM-Node1", flush=True)
    time.sleep(5)

    monitor = subprocess.Popen([
        sys.executable,
        str(SCRIPTS / "monitor_disponibilidad_integral.py")
    ], stdout=subprocess.DEVNULL)

    print("Monitor de disponibilidad iniciado", flush=True)

    comando = [
        sys.executable,
        str(SCRIPTS / "controlador_pcm_v5.py")
    ]

    if args.autorizar_conmutacion:
        comando.append("--autorizar-conmutacion")

    print("Ejecutando controlador...", flush=True)

    with open(log, "w", encoding="utf-8") as archivo:
        resultado = subprocess.run(
            comando,
            stdout=archivo,
            stderr=subprocess.STDOUT,
            timeout=110
        )

    print(log.read_text(), flush=True)

    monitor.wait(timeout=120)

    origen = RESULTADOS / "monitor_disponibilidad_integral.csv"
    destino = RESULTADOS / ("disponibilidad_v5_" + fecha + ".csv")

    if not origen.exists():
        raise RuntimeError("No se genero el archivo de disponibilidad")

    destino.write_bytes(origen.read_bytes())

    with open(destino, newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))

    exitosas = sum(f["resultado"] == "exitoso" for f in filas)
    fallidas = len(filas) - exitosas

    print("=== RESUMEN ===")
    print("Solicitudes:", len(filas))
    print("Exitosas:", exitosas)
    print("Fallidas:", fallidas)
    print("Controlador:", resultado.returncode)
    print("Log:", log)
    print("CSV:", destino)

    if resultado.returncode != 0 or fallidas:
        sys.exit(1)

except Exception as error:
    print("ERROR:", error)
    sys.exit(1)

finally:
    detener(monitor)
    detener(carga)
