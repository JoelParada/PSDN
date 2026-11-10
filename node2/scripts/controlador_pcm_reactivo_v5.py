#!/usr/bin/env python3

import argparse
import csv
import math
import subprocess
import sys
from pathlib import Path

from detectar_nodo_activo import obtener_nodo_activo
from verificar_destino import verificar_http
from verificar_recursos_destino import consultar_recursos
from verificar_recursos_globales import consultar_recursos as consultar_globales

BASE = Path.home() / "pcm-orquestador"
SCRIPTS = BASE / "scripts"
UMBRAL_CPU = 80.0

def ejecutar(comando):
    subprocess.run(comando, check=True)

def obtener_cpu_real():
    ejecutar([
        sys.executable,
        str(SCRIPTS / "recolectar_cpu_cgroup.py")
    ])

    archivo = BASE / "metricas/cpu_cgroup_carga.csv"

    with archivo.open(newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    if not filas:
        raise RuntimeError("No existen mediciones de CPU")

    valores = []

    for fila in filas:
        if "cpu_pct" in fila:
            cpu = float(fila["cpu_pct"])
        elif "cpu_percent" in fila:
            cpu = float(fila["cpu_percent"])
        else:
            raise RuntimeError("Columna de CPU no reconocida")

        if not math.isfinite(cpu) or cpu < 0:
            raise ValueError("Medicion de CPU invalida")

        valores.append(cpu)

    if len(valores) != 10:
        raise RuntimeError("Se requieren exactamente 10 mediciones reales")

    superiores = sum(cpu > UMBRAL_CPU for cpu in valores)

    print("CPU promedio: {:.3f}%".format(sum(valores) / len(valores)))
    print("CPU maxima: {:.3f}%".format(max(valores)))
    print("Mediciones superiores al 80%: {}/10".format(superiores))

    return superiores


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--autorizar-conmutacion",
        action="store_true"
    )

    args = parser.parse_args()

    print("=== CONTROLADOR REACTIVO PCM V5 ===", flush=True)

    nodo = obtener_nodo_activo()
    print("Nodo activo:", nodo)

    if nodo != "pcm-node1":
        print("SIN CONMUTACION: PCM-Node1 no esta activo")
        return 0

    print("\n1. Recolectando CPU real...", flush=True)
    superiores = obtener_cpu_real()

    print("Criterio reactivo: al menos 7 de 10 mediciones")
    print("Umbral: {:.1f}%".format(UMBRAL_CPU))

    if superiores < 7:
        print("DECISION: MANTENER CONFIGURACION")
        return 0

    print("DECISION: CANDIDATO A CONMUTACION HACIA PCM-NODE3")

    print("\n2. Verificando destino...", flush=True)

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
        raise RuntimeError("El nodo activo cambio")

    print("\n3. Ejecutando conmutacion...", flush=True)

    ejecutar([
        sys.executable,
        str(SCRIPTS / "cambiar_trafico.py"),
        "node3"
    ])

    if obtener_nodo_activo() != "pcm-node3":
        raise RuntimeError("No se confirmo el nodo destino")

    print("CONMUTACION REACTIVA EXITOSA")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("ERROR:", error)
        print("CONTROLADOR REACTIVO DETENIDO POR SEGURIDAD")
        sys.exit(1)
