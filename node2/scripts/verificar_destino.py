#!/usr/bin/env python3

import math
import sys
import urllib.request

from verificar_recursos_destino import consultar_recursos
from verificar_recursos_globales import consultar_recursos as consultar_globales

URL_DESTINO = "http://192.168.56.13:5001/"

CPU_CONTENEDOR_MAX = 70.0
RAM_CONTENEDOR_MAX = 80.0
CPU_GLOBAL_MAX = 70.0
RAM_DISPONIBLE_MIN = 20.0


def verificar_http():
    with urllib.request.urlopen(URL_DESTINO, timeout=5) as respuesta:
        if respuesta.status != 200:
            raise RuntimeError("HTTP diferente de 200")

        import json
        datos = json.load(respuesta)

        if datos.get("nodo") != "pcm-node3":
            raise RuntimeError("Identidad del destino incorrecta")

        if datos.get("estado") != "funcionando":
            raise RuntimeError("Aplicacion no disponible")


def main():
    print("=== VERIFICACION INTEGRAL PCM-NODE3 ===")

    try:
        verificar_http()
        print("HTTP destino: CORRECTO")

        cpu_c, ram_c = consultar_recursos()
        cpu_g, ram_g, nucleos = consultar_globales()

        valores = (cpu_c, ram_c, cpu_g, ram_g)

        if not all(math.isfinite(x) for x in valores):
            raise ValueError("Metricas invalidas")

        print("CPU contenedor: {:.2f}%".format(cpu_c))
        print("RAM contenedor: {:.2f}%".format(ram_c))
        print("CPU global: {:.2f}%".format(cpu_g))
        print("RAM global disponible: {:.2f}%".format(ram_g))
        print("Nucleos:", nucleos)

        apto = (
            cpu_c < CPU_CONTENEDOR_MAX
            and ram_c < RAM_CONTENEDOR_MAX
            and cpu_g < CPU_GLOBAL_MAX
            and ram_g > RAM_DISPONIBLE_MIN
        )

        if apto:
            print("Resultado: VERIFICACIONES PRELIMINARES APROBADAS")
            print("No autoriza por si solo una conmutacion.")
            return 0

        print("Resultado: DESTINO NO APTO SEGUN LIMITES")
        return 1

    except Exception as error:
        print("ERROR:", error)
        print("Resultado: DESTINO NO VERIFICADO")
        return 1


if __name__ == "__main__":
    sys.exit(main())
