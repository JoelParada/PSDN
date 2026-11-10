#!/usr/bin/env python3

import csv
import math
from collections import defaultdict
from pathlib import Path

BASE = Path.home() / "pcm-orquestador"
DATASET = BASE / "datos_evaluacion" / "dataset_maestro_pcm_v5.csv"
SALIDA = BASE / "datos_evaluacion" / "baseline_persistencia_v5.csv"

VENTANA = 10
UMBRAL = 80.0

grupos = defaultdict(list)

with DATASET.open(newline="", encoding="utf-8") as archivo:
    for fila in csv.DictReader(archivo):
        grupos[fila["experimento_id"]].append(fila)

resultados = []

for nombre, filas in grupos.items():
    filas.sort(key=lambda f: f["timestamp"])

    valores = [float(f["cpu_pct"]) for f in filas]

    if len(valores) <= VENTANA + 2:
        continue

    corte = max(VENTANA + 1, int(len(valores) * 0.8))

    for i in range(VENTANA, len(valores)):
        if i < corte:
            continue

        cpu_real = valores[i]
        cpu_predicha = valores[i - 1]
        error = abs(cpu_real - cpu_predicha)

        decision = (
            "CANDIDATO_CONMUTACION"
            if cpu_predicha >= UMBRAL
            else "MANTENER_NODO"
        )

        resultados.append([
            nombre,
            filas[i]["timestamp"],
            cpu_real,
            cpu_predicha,
            error,
            decision
        ])

if not resultados:
    raise SystemExit("ERROR: no se encontraron secuencias de prueba")

with SALIDA.open("w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo)

    escritor.writerow([
        "experimento_id",
        "timestamp",
        "cpu_real",
        "cpu_predicha_baseline",
        "error_absoluto",
        "decision_baseline"
    ])

    escritor.writerows(resultados)

errores = [fila[4] for fila in resultados]

mae = sum(errores) / len(errores)

rmse = math.sqrt(
    sum(error ** 2 for error in errores) / len(errores)
)

print("=== BASELINE TRADICIONAL PCM ===")
print("Metodo: Persistencia")
print("Secuencias evaluadas:", len(resultados))
print(f"MAE: {mae:.4f} puntos porcentuales")
print(f"RMSE: {rmse:.4f} puntos porcentuales")
print("Archivo:", SALIDA)
print("BASELINE EJECUTADO CORRECTAMENTE")
