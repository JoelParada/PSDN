#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

BASE = Path.home() / "pcm-orquestador" / "scripts"


def ejecutar(nombre):
    print("\nEjecutando:", nombre, flush=True)

    resultado = subprocess.run(
        [sys.executable, str(BASE / nombre)],
        check=False
    )

    if resultado.returncode != 0:
        print("ERROR: fallo en", nombre, flush=True)
        return False

    return True


def main():
    print("=== CICLO INTEGRADO PCM SEGURO ===", flush=True)

    if not ejecutar("ciclo_prediccion.py"):
        print("Ciclo detenido: prediccion no disponible")
        return 1

    if not ejecutar("evaluar_migracion_segura.py"):
        print("Ciclo detenido: evaluacion no aprobada")
        return 1

    print("\nCICLO PCM COMPLETADO")
    print("Modo: SOLO EVALUACION")
    print("No se realizaron cambios de trafico.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
