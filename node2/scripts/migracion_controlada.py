#!/usr/bin/env python3

import json
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "pcm-orquestador"
CONFIG = BASE / "config" / "migracion.json"

with open(CONFIG, encoding="utf-8") as archivo:
    cfg = json.load(archivo)


def ejecutar_ssh(nodo, comando):
    resultado = subprocess.run(
        [
            "ssh",
            "-i", nodo["ssh_key"],
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            nodo["usuario"] + "@" + nodo["ip"],
            comando
        ],
        capture_output=True,
        text=True,
        timeout=15
    )

    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip())

    return resultado.stdout.strip()


def verificar_http(nodo, puerto):
    url = "http://{}:{}{}".format(
        nodo["ip"],
        puerto,
        cfg["healthcheck"]["ruta"]
    )

    with urllib.request.urlopen(
        url,
        timeout=cfg["healthcheck"]["timeout_segundos"]
    ) as respuesta:
        contenido = json.loads(respuesta.read().decode())

        if respuesta.status != 200:
            raise RuntimeError("HTTP diferente de 200")

        if contenido.get("nodo") != nodo["nombre"]:
            raise RuntimeError("Identificador del nodo incorrecto")

        return contenido


def main():
    print("=== ORQUESTADOR PCM ===")
    print("Fecha:", datetime.now().isoformat(timespec="seconds"))
    print("Modo: VERIFICACION SEGURA")
    print()

    origen = cfg["origen"]
    destino = cfg["destino"]

    print("[1] Verificando contenedor origen...")
    estado = ejecutar_ssh(
        origen,
        "docker inspect {} --format '{{{{.State.Status}}}}'".format(
            origen["contenedor"]
        )
    )
    print("Estado:", estado)

    if estado != "running":
        raise RuntimeError("El contenedor origen no esta activo")

    print("\n[2] Verificando HTTP origen...")
    print(verificar_http(origen, origen["puerto"]))

    print("\n[3] Verificando contenedor de prueba destino...")
    estado = ejecutar_ssh(
        destino,
        "docker inspect {} --format '{{{{.State.Status}}}}'".format(
            destino["contenedor_prueba"]
        )
    )
    print("Estado:", estado)

    if estado != "running":
        raise RuntimeError("El contenedor de prueba no esta activo")

    print("\n[4] Verificando HTTP destino...")
    print(verificar_http(destino, destino["puerto_prueba"]))

    print("\n=== RESULTADO ===")
    print("PREPARADO: Origen y destino responden correctamente")
    print("No se modificaron contenedores")
    print("No se ejecuto ninguna migracion")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\nERROR:", error)
        raise SystemExit(1)
