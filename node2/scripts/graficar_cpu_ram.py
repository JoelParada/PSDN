#!/usr/bin/env python3

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path.home() / "pcm-orquestador"
ARCHIVO = BASE / "datos_evaluacion" / "dataset_maestro_pcm_v5.csv"
SALIDA = BASE / "graficas"
SALIDA.mkdir(parents=True, exist_ok=True)

experimentos = defaultdict(list)

with open(ARCHIVO, newline="", encoding="utf-8") as f:
    for fila in csv.DictReader(f):
        experimentos[fila["experimento_id"]].append(fila)

print("=== GENERACION DE GRAFICAS PCM ===")
print("Experimentos encontrados:", len(experimentos))

for variable, titulo, nombre in [
    ("cpu_pct", "Utilizacion real de CPU", "serie_temporal_cpu.png"),
    ("ram_pct", "Utilizacion real de RAM", "serie_temporal_ram.png"),
]:
    fig, ax = plt.subplots(figsize=(12, 5))

    posicion = 0
    separaciones = []

    for identificador, filas in experimentos.items():
        filas.sort(
            key=lambda f: (
                f["timestamp"],
                float(f["segundos_desde_inicio"])
                if f["segundos_desde_inicio"].strip()
                else 0.0
            )
        )

        valores = []
        posiciones = []
        faltantes = 0

        for indice, fila in enumerate(filas):
            dato = fila[variable].strip()

            if not dato:
                faltantes += 1
                continue

            try:
                valor = float(dato)
            except ValueError:
                faltantes += 1
                continue

            valores.append(valor)
            posiciones.append(posicion + indice)

        if faltantes:
            print(
                identificador,
                "-",
                variable,
                "- mediciones sin dato:",
                faltantes
            )

        ax.plot(
            posiciones,
            valores,
            linewidth=1.5,
            label=identificador
        )

        posicion += len(valores)
        separaciones.append(posicion)
        posicion += 2

    for separacion in separaciones[:-1]:
        ax.axvline(
            separacion,
            color="gray",
            linestyle=":",
            alpha=0.4
        )

    ax.set_title(titulo + " - PCM LSTM V5")
    ax.set_xlabel("Indice de medicion (experimentos separados)")
    ax.set_ylabel("Utilizacion (%)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()

    destino = SALIDA / nombre
    fig.savefig(destino, dpi=180)
    plt.close(fig)

    print("Grafica generada:", destino)

print("PROCESO FINALIZADO")
