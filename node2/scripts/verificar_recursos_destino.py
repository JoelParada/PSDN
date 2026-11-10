#!/usr/bin/env python3

import subprocess
import sys
import math

SSH_KEY = "/home/pcmadmin/.ssh/pcm_node3_ed25519"
SERVIDOR = "pcmadmin@192.168.56.13"
CONTENEDOR = "pcm-flask-migracion-test"

UMBRAL_CPU = 70.0
UMBRAL_RAM = 80.0


def consultar_recursos():
    comando = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        "-i", SSH_KEY,
        SERVIDOR,
        "docker stats --no-stream "
        "--format '{{.CPUPerc}}|{{.MemPerc}}' "
        + CONTENEDOR
    ]

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        timeout=20,
        check=True
    )

    lineas = resultado.stdout.strip().splitlines()

    if len(lineas) != 1:
        raise RuntimeError("Respuesta inesperada de Docker")

    valores = lineas[0].split("|")

    if len(valores) != 2:
        raise RuntimeError("Formato de metricas invalido")

    cpu = float(valores[0].strip().replace("%", ""))
    ram = float(valores[1].strip().replace("%", ""))

    if not all(math.isfinite(x) for x in (cpu, ram)):
        raise ValueError("Metricas no validas")

    if cpu < 0 or ram < 0 or ram > 100:
        raise ValueError("Metricas fuera de rango")

    return cpu, ram


def main():
    print("=== VERIFICACION DE RECURSOS PCM-NODE3 ===")

    try:
        cpu, ram = consultar_recursos()

        print("CPU destino: {:.2f}%".format(cpu))
        print("RAM destino: {:.2f}%".format(ram))

        if cpu < UMBRAL_CPU and ram < UMBRAL_RAM:
            print("Resultado: RECURSOS DENTRO DE LIMITES")
        else:
            print("Resultado: REQUIERE REVISION DE RECURSOS")

        print("Modo: SOLO VERIFICACION")
        return 0

    except Exception as error:
        print("ERROR:", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
