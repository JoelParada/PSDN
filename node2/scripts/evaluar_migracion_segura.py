#!/usr/bin/env python3

import sys

from consultar_lstm_v5 import obtener_prediccion
from detectar_nodo_activo import obtener_nodo_activo
from evaluar_migracion import decidir_migracion
from verificar_destino import verificar_http
from verificar_recursos_destino import consultar_recursos
from verificar_recursos_globales import consultar_recursos as consultar_globales

CPU_CONTENEDOR_MAX = 70.0
RAM_CONTENEDOR_MAX = 80.0
CPU_GLOBAL_MAX = 70.0
RAM_DISPONIBLE_MIN = 20.0


def main():
    print("=== EVALUACION SEGURA PCM ===", flush=True)

    try:
        nodo = obtener_nodo_activo()
        prediccion = obtener_prediccion()
        decision = decidir_migracion(prediccion, nodo)

        print("Nodo activo:", nodo)
        print("CPU predicha: {:.3f}%".format(prediccion))
        print("Decision inicial:", decision)

        if decision != "CANDIDATO A CONMUTACION HACIA PCM-NODE3":
            print("Resultado: SIN CONMUTACION")
            print("Modo: SOLO EVALUACION")
            return 0

        print("\nVerificando destino PCM-Node3...")

        verificar_http()
        cpu_c, ram_c = consultar_recursos()
        cpu_g, ram_g, nucleos = consultar_globales()

        print("HTTP destino: CORRECTO")
        print("CPU contenedor: {:.2f}%".format(cpu_c))
        print("RAM contenedor: {:.2f}%".format(ram_c))
        print("CPU global: {:.2f}%".format(cpu_g))
        print("RAM disponible: {:.2f}%".format(ram_g))
        print("Nucleos:", nucleos)

        apto = (
            cpu_c < CPU_CONTENEDOR_MAX
            and ram_c < RAM_CONTENEDOR_MAX
            and cpu_g < CPU_GLOBAL_MAX
            and ram_g > RAM_DISPONIBLE_MIN
        )

        if not apto:
            print("Resultado: CONMUTACION BLOQUEADA")
            return 1

        print("Resultado: CANDIDATO CON VERIFICACIONES PRELIMINARES")
        print("Pendiente: validacion predictiva y pruebas de carga")
        print("No se realizaron cambios de trafico.")
        return 0

    except Exception as error:
        print("ERROR:", error)
        print("Resultado: CONMUTACION BLOQUEADA")
        return 1


if __name__ == "__main__":
    sys.exit(main())
