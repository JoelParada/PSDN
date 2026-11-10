#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

BASE = Path("/home/pcmadmin/pcm-orquestador/scripts")

ETAPAS = [
    ("RECOLECCION DE CPU", "recolectar_cpu.py"),
    ("ACTUALIZACION DE METRICAS", "actualizar_metricas_lstm.py"),
    ("PREDICCION LSTM V4", "consultar_lstm.py"),
]

def main():
    print("=== CICLO DE PREDICCION PCM ===", flush=True)

    for nombre, archivo in ETAPAS:
        print("\n>>> " + nombre, flush=True)

        resultado = subprocess.run(
            [sys.executable, str(BASE / archivo)],
            check=False
        )

        if resultado.returncode != 0:
            print(
                "\nERROR: Fallo la etapa " + nombre,
                flush=True
            )
            print("Ciclo detenido por seguridad.", flush=True)
            return 1

    print("\n=== CICLO COMPLETADO ===", flush=True)
    print("Prediccion generada con nuevas metricas.", flush=True)
    print("No se realizaron cambios de trafico.", flush=True)

    return 0

if __name__ == "__main__":
    sys.exit(main())
