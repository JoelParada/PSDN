#!/usr/bin/env python3

import sys
import math

from consultar_lstm import obtener_prediccion
from detectar_nodo_activo import obtener_nodo_activo

UMBRAL_OPERATIVO = 80.0


def decidir_migracion(prediccion, nodo_activo):
    if not math.isfinite(prediccion):
        raise ValueError("Prediccion de CPU invalida")

    if nodo_activo not in ("pcm-node1", "pcm-node3"):
        raise ValueError("Nodo activo no reconocido")

    if prediccion < UMBRAL_OPERATIVO:
        return "MANTENER CONFIGURACION ACTUAL"

    if nodo_activo == "pcm-node3":
        return "NO CONMUTAR: DESTINO YA ACTIVO"

    return "CANDIDATO A CONMUTACION HACIA PCM-NODE3"


def main():
    print("=== EVALUACION INTELIGENTE PCM ===")

    try:
        nodo_activo = obtener_nodo_activo()
        prediccion = obtener_prediccion()

        decision = decidir_migracion(
            prediccion,
            nodo_activo
        )

        print("Nodo activo configurado:", nodo_activo)
        print("CPU predicha: {:.3f}%".format(prediccion))
        print("Umbral operativo propuesto: {:.1f}%".format(
            UMBRAL_OPERATIVO
        ))
        print("Decision:", decision)

        print("Modo: SOLO EVALUACION")
        print("No se realizaron cambios de trafico.")

        return 0

    except Exception as error:
        print("ERROR:", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
