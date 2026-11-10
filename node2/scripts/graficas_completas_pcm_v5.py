#!/usr/bin/env python3

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BASE = Path.home() / "pcm-orquestador"
ORIG = BASE / "datos_evaluacion"
NUEVOS = BASE / "experimentos_v5_nuevos/datos"
SALIDA = BASE / "experimentos_v5_nuevos/graficas"
SALIDA.mkdir(parents=True, exist_ok=True)

def leer(ruta):
    with ruta.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

originales = defaultdict(list)

for fila in leer(ORIG / "dataset_maestro_pcm_v5.csv"):
    originales[fila["experimento_id"]].append(fila)

for filas in originales.values():
    filas.sort(key=lambda f: f["timestamp"])

nuevos = {}

for escenario in ("growth", "spike"):
    archivos_definitivos = {
        "growth": "growth_v5_20261110_020233.csv",
        "spike": "spike_v5_20261110_020639.csv"
    }

    archivo = NUEVOS / archivos_definitivos[escenario]

    if not archivo.is_file():
        raise RuntimeError(f"No existe el archivo: {archivo}")

    nuevos[escenario] = leer(archivo)

pred_originales = defaultdict(list)

for fila in leer(ORIG / "predicciones_vs_reales_v5.csv"):
    pred_originales[fila["experimento_id"]].append(fila)

for filas in pred_originales.values():
    filas.sort(key=lambda f: f["timestamp"])

pred_nuevas = defaultdict(list)

for fila in leer(NUEVOS / "predicciones_nuevas_v5.csv"):
    pred_nuevas[fila["escenario"]].append(fila)

for filas in pred_nuevas.values():
    filas.sort(key=lambda f: f["timestamp"])

# Mantener el orden de los experimentos originales.
orden = list(originales.keys())

# Los experimentos nuevos se agregan al final.
orden += ["growth_v5_nuevo", "spike_v5_nuevo"]

series = {}

for nombre in originales:
    series[nombre] = {
        "cpu": [float(f["cpu_pct"]) for f in originales[nombre]],
        "ram_pct": [float(f["ram_pct"]) if f["ram_pct"].strip() else float("nan") for f in originales[nombre]],
        "ram_mib": None
    }

for escenario in ("growth", "spike"):
    nombre = f"{escenario}_v5_nuevo"

    series[nombre] = {
        "cpu": [float(f["cpu_pct"]) for f in nuevos[escenario]],
        "ram_pct": None,
        "ram_mib": [float(f["ram_mib"]) for f in nuevos[escenario]]
    }

posiciones = {}
separadores = []
inicio = 0
espacio = 3

for nombre in orden:
    cantidad = len(series[nombre]["cpu"])
    posiciones[nombre] = list(range(inicio, inicio + cantidad))
    inicio += cantidad
    separadores.append(inicio + espacio / 2)
    inicio += espacio

colores = plt.get_cmap("tab20")

def preparar_eje(ax):
    for separador in separadores[:-1]:
        ax.axvline(
            separador,
            color="gray",
            linestyle=":",
            alpha=0.35
        )
    ax.grid(alpha=0.25)
    ax.set_xticks([
        (posiciones[n][0] + posiciones[n][-1]) / 2
        for n in orden
    ])
    ax.set_xticklabels(
        orden,
        rotation=48,
        ha="right",
        fontsize=8
    )

# =========================================================
# GRAFICA 1: CPU REAL VS LSTM V5
# =========================================================

fig, ax = plt.subplots(figsize=(22, 8))

errores = []

for nombre, filas in pred_originales.items():
    if nombre not in posiciones:
        continue

    indices = {
        fila["timestamp"]: x
        for x, fila in zip(posiciones[nombre], originales[nombre])
    }

    datos = [
        (indices[f["timestamp"]], f)
        for f in filas
        if f["timestamp"] in indices
    ]

    if not datos:
        continue

    x = [p[0] for p in datos]
    real = [float(p[1]["cpu_real"]) for p in datos]
    pred = [float(p[1]["cpu_predicha"]) for p in datos]

    ax.plot(x, real, color="#2563eb", linewidth=2)
    ax.plot(x, pred, color="#dc2626", linestyle="--", linewidth=2)

    errores.extend((r-p)**2 for r, p in zip(real, pred))

for escenario in ("growth", "spike"):
    nombre = f"{escenario}_v5_nuevo"

    indices = {
        fila["timestamp"]: x
        for x, fila in zip(posiciones[nombre], nuevos[escenario])
    }

    datos = [
        (indices[f["timestamp"]], f)
        for f in pred_nuevas[escenario]
        if f["timestamp"] in indices
    ]

    x = [p[0] for p in datos]
    real = [float(p[1]["cpu_real"]) for p in datos]
    pred = [float(p[1]["cpu_predicha_lstm"]) for p in datos]

    ax.plot(x, real, color="#2563eb", linewidth=2.5)
    ax.plot(x, pred, color="#dc2626", linestyle="--", linewidth=2.5)

ax.axhline(
    80, color="#16a34a", linestyle="-.",
    linewidth=1.8
)

preparar_eje(ax)

ax.set_title(
    "PCM - Comparacion de CPU real vs. predicha por LSTM V5\n"
    "102 secuencias originales + 15 predicciones nuevas",
    fontsize=16
)
ax.set_ylabel("Utilizacion de CPU (%)")
ax.set_xlabel("Secuencia de prueba (experimentos separados)")
ax.set_ylim(-4, 105)

ax.legend(handles=[
    Line2D([0], [0], color="#2563eb", lw=2, label="CPU real"),
    Line2D([0], [0], color="#dc2626", lw=2,
           linestyle="--", label="CPU predicha LSTM V5"),
    Line2D([0], [0], color="#16a34a", lw=2,
           linestyle="-.", label="Umbral operativo: 80 %")
], loc="upper left")

fig.tight_layout()
fig.savefig(
    SALIDA / "01_cpu_real_vs_predicha_lstm_v5_completa.png",
    dpi=200
)
plt.close(fig)

# =========================================================
# GRAFICA 2: CPU REAL DE TODOS LOS EXPERIMENTOS
# =========================================================

fig, ax = plt.subplots(figsize=(22, 8))

for i, nombre in enumerate(orden):
    ax.plot(
        posiciones[nombre],
        series[nombre]["cpu"],
        color=colores(i % 20),
        linewidth=2,
        label=nombre
    )

preparar_eje(ax)

ax.axhline(
    80, color="black", linestyle="--",
    alpha=0.6, label="Umbral 80 %"
)

ax.set_title(
    "Utilizacion real de CPU - PCM LSTM V5",
    fontsize=18
)
ax.set_xlabel("Indice de medicion (experimentos separados)")
ax.set_ylabel("Utilizacion (%)")
ax.set_ylim(-4, 105)
ax.legend(loc="upper left", fontsize=8, ncol=2)

fig.tight_layout()
fig.savefig(
    SALIDA / "02_serie_temporal_cpu_completa.png",
    dpi=200
)
plt.close(fig)

# =========================================================
# GRAFICA 3: RAM REAL, UNIDADES CORRECTAS
# =========================================================

fig, ax = plt.subplots(figsize=(22, 8))
ax2 = ax.twinx()

for i, nombre in enumerate(orden):
    color = colores(i % 20)

    if series[nombre]["ram_pct"] is not None:
        ax.plot(
            posiciones[nombre],
            series[nombre]["ram_pct"],
            color=color,
            linewidth=2,
            label=nombre
        )
    else:
        ax2.plot(
            posiciones[nombre],
            series[nombre]["ram_mib"],
            color=color,
            linewidth=2.5,
            linestyle="--",
            label=nombre + " (MiB)"
        )

preparar_eje(ax)

ax.set_title(
    "Utilizacion real de RAM - PCM LSTM V5",
    fontsize=18
)
ax.set_xlabel("Indice de medicion (experimentos separados)")
ax.set_ylabel("RAM original (%)")
ax2.set_ylabel("RAM nueva (MiB)")

lineas1, etiquetas1 = ax.get_legend_handles_labels()
lineas2, etiquetas2 = ax2.get_legend_handles_labels()

ax.legend(
    lineas1 + lineas2,
    etiquetas1 + etiquetas2,
    loc="upper left",
    fontsize=8,
    ncol=2
)

fig.tight_layout()
fig.savefig(
    SALIDA / "03_serie_temporal_ram_completa.png",
    dpi=200
)
plt.close(fig)

print("=== TRES GRAFICAS COMPLETAS GENERADAS ===")
print("Experimentos originales:", len(originales))
print("Experimentos nuevos:", len(nuevos))
print("Predicciones originales:", sum(map(len, pred_originales.values())))
print("Predicciones nuevas:", sum(map(len, pred_nuevas.values())))

for archivo in sorted(SALIDA.glob("*completa.png")):
    print(archivo)
