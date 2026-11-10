#!/usr/bin/env python3

import subprocess
import sys

SSH_KEY = "/home/pcmadmin/.ssh/pcm_node3_ed25519"
SERVIDOR = "pcmadmin@192.168.56.13"

def consultar_recursos():
    comando_remoto = (
        "LC_ALL=C top -bn1 | grep '%Cpu'; "
        "free -m | grep '^Mem:'; "
        "nproc"
    )

    resultado = subprocess.run(
        [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            "-i", SSH_KEY,
            SERVIDOR,
            comando_remoto
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=True
    )

    lineas = resultado.stdout.strip().splitlines()

    if len(lineas) != 3:
        raise RuntimeError("Respuesta inesperada del nodo")

    import re

    coincidencia = re.search(
        r"([\d.]+)\s+id",
        lineas[0]
    )

    if not coincidencia:
        raise RuntimeError("No se pudo interpretar la CPU")

    cpu_uso = 100.0 - float(coincidencia.group(1))

    memoria = lineas[1].split()

    ram_total = int(memoria[1])
    ram_disponible = int(memoria[6])
    nucleos = int(lineas[2])

    if ram_total <= 0 or nucleos <= 0:
        raise ValueError("Recursos invalidos")

    if not (0 <= cpu_uso <= 100):
        raise ValueError("CPU fuera de rango")

    if not (0 <= ram_disponible <= ram_total):
        raise ValueError("RAM fuera de rango")

    ram_disponible_pct = (
        ram_disponible / ram_total
    ) * 100

    return cpu_uso, ram_disponible_pct, nucleos


def main():
    print("=== RECURSOS GLOBALES PCM-NODE3 ===")

    try:
        cpu, ram, nucleos = consultar_recursos()

        print("CPU global utilizada: {:.2f}%".format(cpu))
        print("RAM disponible: {:.2f}%".format(ram))
        print("Nucleos CPU:", nucleos)

        print("Modo: SOLO VERIFICACION")
        return 0

    except Exception as error:
        print("ERROR:", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
