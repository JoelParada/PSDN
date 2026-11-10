#!/usr/bin/env python3

import argparse
import math
import time
import subprocess
import sys
from pathlib import Path

from consultar_lstm_v5 import obtener_prediccion
from detectar_nodo_activo import obtener_nodo_activo
from evaluar_migracion import decidir_migracion
from verificar_destino import verificar_http
from verificar_recursos_destino import consultar_recursos
from verificar_recursos_globales import consultar_recursos as consultar_globales

BASE = Path.home() / "pcm-orquestador"
SCRIPTS = BASE / "scripts"

def ejecutar(comando):
    subprocess.run(comando, check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--autorizar-conmutacion",
        action="store_true"
    )
    parser.add_argument(
        "--simular-prediccion",
        type=float,
        default=None,
        help="Prediccion simulada para prueba funcional"
    )
    args = parser.parse_args()

    print("=== CONTROLADOR INTEGRADO PCM V5 ===", flush=True)

    nodo = obtener_nodo_activo()
    print("Nodo activo:", nodo, flush=True)

    if nodo != "pcm-node1":
        print("SIN CONMUTACION: el monitoreo actual corresponde a PCM-Node1")
        print("Se evita tomar decisiones con metricas del nodo inactivo")
        return 0

    print("\n1. Recolectando metricas...", flush=True)
    ejecutar([
        sys.executable,
        str(SCRIPTS / "recolectar_cpu_cgroup.py")
    ])

    print("\n2. Transfiriendo metricas...", flush=True)
    ejecutar([
        "scp",
        "-i", str(Path.home() / ".ssh/pcm_node1_ed25519"),
        str(BASE / "metricas/cpu_cgroup_carga.csv"),
        "pcmadmin@192.168.56.11:/home/pcmadmin/pcm-lstm/cpu_tiempo_real.csv"
    ])

    print("\n3. Verificando frescura de metricas...", flush=True)

    archivo_metricas = BASE / "metricas/cpu_cgroup_carga.csv"
    antiguedad = time.time() - archivo_metricas.stat().st_mtime

    if antiguedad < 0 or antiguedad > 120:
        raise RuntimeError(
            "Metricas antiguas o fecha invalida: {:.1f} segundos".format(
                antiguedad
            )
        )

    print("Antiguedad: {:.1f} segundos".format(antiguedad))

    print("\n4. Ejecutando LSTM V5...", flush=True)
    if args.simular_prediccion is not None:
        if not args.autorizar_conmutacion:
            raise RuntimeError(
                "La simulacion requiere autorizacion explicita"
            )
        print("MODO PRUEBA: PREDICCION SIMULADA", flush=True)
        prediccion = args.simular_prediccion
    else:
        prediccion = obtener_prediccion()

    if not math.isfinite(prediccion):
        raise ValueError("Prediccion no valida")

    decision = decidir_migracion(prediccion, nodo)

    print("CPU predicha: {:.3f}%".format(prediccion))
    print("Decision:", decision)

    if decision != "CANDIDATO A CONMUTACION HACIA PCM-NODE3":
        print("RESULTADO: MANTENER CONFIGURACION")
        return 0

    print("\n4. Verificando PCM-Node3...", flush=True)

    verificar_http()
    cpu_c, ram_c = consultar_recursos()
    cpu_g, ram_g, nucleos = consultar_globales()

    print("CPU contenedor: {:.2f}%".format(cpu_c))
    print("RAM contenedor: {:.2f}%".format(ram_c))
    print("CPU global: {:.2f}%".format(cpu_g))
    print("RAM disponible: {:.2f}%".format(ram_g))
    print("Nucleos:", nucleos)

    apto = (
        cpu_c < 70
        and ram_c < 80
        and cpu_g < 70
        and ram_g > 20
    )

    if not apto:
        print("RESULTADO: CONMUTACION BLOQUEADA")
        return 1

    print("RESULTADO: DESTINO APTO")

    if not args.autorizar_conmutacion:
        print("MODO SEGURO: CONMUTACION NO AUTORIZADA")
        return 0

    if obtener_nodo_activo() != "pcm-node1":
        raise RuntimeError("El nodo activo cambio durante la evaluacion")

    print("\n5. Ejecutando conmutacion supervisada...", flush=True)

    ejecutar([
        sys.executable,
        str(SCRIPTS / "cambiar_trafico.py"),
        "node3"
    ])

    if obtener_nodo_activo() != "pcm-node3":
        raise RuntimeError("No se confirmo el nodo destino")

    print("CONMUTACION SUPERVISADA EXITOSA")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("ERROR:", error)
        print("CONTROLADOR DETENIDO POR SEGURIDAD")
        sys.exit(1)
