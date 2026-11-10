#!/usr/bin/env python3

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path.home() / "pcm-orquestador"
ARCHIVO = BASE / "datos_evaluacion" / "predicciones_vs_reales_v5.csv"
SALIDA = BASE / "graficas"
SALIDA.mkdir(parents=True, exist_ok=True)

grupos = defaultdict(list)

with ARCHIVO.open(newline="", encoding="utf-8") as archivo:
    for fila in csv.DictReader(archivo):
        grupos[fila["experimento_id"]].append(fila)

fig, ax = plt.subplots(figsize=(15, 6))

todos_reales = []
todos_predichos = []

posicion = 0
centros = []
etiquetas = []

for nombre, filas in grupos.items():

    filas.sort(key=lambda f: f["timestamp"])

    reales = [float(f["cpu_real"]) for f in filas]
    predichos = [float(f["cpu_predicha"]) for f in filas]

    posiciones = list(range(posicion, posicion + len(filas)))

    ax.plot(
        posiciones,
        reales,
        color="#2563eb",
        linewidth=1.8,
        label="CPU real" if posicion == 0 else None
    )

    ax.plot(
        posiciones,
        predichos,
        color="#dc2626",
        linestyle="--",
        linewidth=1.8,
        label="CPU predicha LSTM V5" if posicion == 0 else None
    )

    centros.append(posicion + (len(filas) - 1) / 2)
    etiquetas.append(nombre)

    todos_reales.extend(reales)
    todos_predichos.extend(predichos)

    posicion += len(filas)

    ax.axvline(
        posicion - 0.5,
        color="gray",
        linestyle=":",
        alpha=0.4
    )

    posicion += 2

ax.axhline(
    80,
    color="#16a34a",
    linestyle="-.",
    linewidth=1.5,
    label="Umbral operativo: 80 %"
)

errores = [
    abs(real - pred)
    for real, pred in zip(todos_reales, todos_predichos)
]

mae = sum(errores) / len(errores)

rmse = math.sqrt(
    sum(
        (real - pred) ** 2
        for real, pred in zip(todos_reales, todos_predichos)
    ) / len(todos_reales)
)

ax.set_title(
    "PCM - Comparacion de CPU real vs. predicha por LSTM V5\n"
    f"102 secuencias de prueba | MAE: {mae:.2f} | RMSE: {rmse:.2f}"
)

ax.set_xlabel("Secuencia de prueba (experimentos separados)")
ax.set_ylabel("Utilizacion de CPU (%)")

ax.set_xticks(centros)
ax.set_xticklabels(etiquetas, rotation=45, ha="right", fontsize=8)

ax.grid(alpha=0.25)
ax.legend(loc="upper left")

fig.tight_layout()

destino = SALIDA / "cpu_real_vs_predicha_lstm_v5.png"

fig.savefig(destino, dpi=200)
plt.close(fig)

print("=== GRAFICA COMPARATIVA LSTM V5 ===")
print("Experimentos evaluados:", len(grupos))
print("Secuencias:", len(todos_reales))
print(f"MAE: {mae:.4f}")
print(f"RMSE: {rmse:.4f}")
print("Grafica generada:", destino)
print("PROCESO FINALIZADO")
