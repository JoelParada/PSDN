#!/usr/bin/env python3

import csv
import json
import time
import urllib.request
from pathlib import Path
from datetime import datetime

URL = "http://192.168.56.12:8081/"
SALIDA = Path.home() / "pcm-orquestador/resultados/monitor_disponibilidad.csv"

INTERVALO = 0.2
DURACION = 20

SALIDA.parent.mkdir(parents=True, exist_ok=True)

print("=== MONITOR DE DISPONIBILIDAD PCM ===")
print("URL:", URL)
print("Duracion:", DURACION, "segundos")
print("Intervalo:", INTERVALO, "segundos")
print("Archivo:", SALIDA)
print()

inicio = time.monotonic()
total = 0
exitosas = 0
fallidas = 0

with open(SALIDA, "w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo)

    escritor.writerow([
        "timestamp",
        "tiempo_relativo_s",
        "http_status",
        "nodo",
        "latencia_ms",
        "resultado"
    ])

    while time.monotonic() - inicio < DURACION:
        instante = time.monotonic()
        timestamp = datetime.now().isoformat(timespec="milliseconds")

        estado = ""
        nodo = ""
        resultado = "fallido"

        try:
            solicitud = urllib.request.Request(
                URL,
                headers={"Connection": "close"}
            )

            with urllib.request.urlopen(
                solicitud, timeout=2
            ) as respuesta:
                estado = respuesta.status
                datos = json.loads(respuesta.read().decode())
                nodo = datos.get("nodo", "")

                if estado == 200 and nodo in ("pcm-node1", "pcm-node3"):
                    resultado = "exitoso"

        except Exception as error:
            estado = str(error)

        latencia = round(
            (time.monotonic() - instante) * 1000, 3
        )

        total += 1

        if resultado == "exitoso":
            exitosas += 1
        else:
            fallidas += 1

        escritor.writerow([
            timestamp,
            round(instante - inicio, 3),
            estado,
            nodo,
            latencia,
            resultado
        ])

        archivo.flush()

        print(
            "Solicitud:", total,
            "| Nodo:", nodo or "sin respuesta",
            "| Resultado:", resultado,
            "| Latencia:", latencia, "ms"
        )

        time.sleep(max(
            0,
            INTERVALO - (time.monotonic() - instante)
        ))

print("\n=== RESULTADOS ===")
print("Solicitudes totales:", total)
print("Exitosas:", exitosas)
print("Fallidas:", fallidas)
print("Disponibilidad observada: {:.2f}%".format(
    (exitosas / total) * 100 if total else 0
))
print("Archivo:", SALIDA)
