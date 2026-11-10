#!/usr/bin/env python3

import sys
import json
import time
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "pcm-orquestador"
CONFIG = BASE / "config" / "migracion.json"
LOG = BASE / "logs" / "cambios_trafico.jsonl"

with open(CONFIG, encoding="utf-8") as archivo:
    cfg = json.load(archivo)

PROXY = "http://192.168.56.12:8081/"

NODOS = {
    "node1": {
        "nombre": cfg["origen"]["nombre"],
        "url": "http://{}:{}/".format(
            cfg["origen"]["ip"],
            cfg["origen"]["puerto"]
        )
    },
    "node3": {
        "nombre": cfg["destino"]["nombre"],
        "url": "http://{}:{}/".format(
            cfg["destino"]["ip"],
            cfg["destino"]["puerto_prueba"]
        )
    }
}


def consultar(url):
    solicitud = urllib.request.Request(
        url,
        headers={"Connection": "close"}
    )
    with urllib.request.urlopen(solicitud, timeout=5) as respuesta:
        if respuesta.status != 200:
            raise RuntimeError("HTTP diferente de 200")
        return json.loads(respuesta.read().decode())


def verificar_nodo(nodo):
    respuesta = consultar(NODOS[nodo]["url"])
    if respuesta.get("nodo") != NODOS[nodo]["nombre"]:
        raise RuntimeError("Identificador incorrecto en " + nodo)
    return respuesta


def detectar_actual():
    respuesta = consultar(PROXY)
    for clave, datos in NODOS.items():
        if respuesta.get("nodo") == datos["nombre"]:
            return clave
    raise RuntimeError("No se reconoce el nodo activo")


def aplicar_cambio(nodo):
    resultado = subprocess.run(
        [
            "sudo", "-n",
            "/usr/local/sbin/pcm-cambiar-nodo",
            nodo
        ],
        capture_output=True,
        text=True,
        timeout=20
    )
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr + resultado.stdout)


def verificar_proxy(nodo):
    for intento in range(10):
        try:
            respuesta = consultar(PROXY)
            if respuesta.get("nodo") == NODOS[nodo]["nombre"]:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("El proxy no responde desde " + nodo)


def registrar(datos):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(datos, ensure_ascii=False) + "\n")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in NODOS:
        print("Uso: python3 cambiar_trafico.py node1|node3")
        return 2

    destino = sys.argv[1]
    inicio = time.monotonic()

    print("=== CAMBIO CONTROLADO DE TRAFICO PCM ===")

    try:
        actual = detectar_actual()
        print("Nodo actual:", actual)
        print("Nodo solicitado:", destino)

        if actual == destino:
            print("El nodo solicitado ya esta activo")
            return 0

        print("Verificando destino...")
        verificar_nodo(destino)

        print("Aplicando cambio de Nginx...")
        aplicar_cambio(destino)

        print("Verificando proxy...")
        verificar_proxy(destino)

        duracion = round(time.monotonic() - inicio, 4)

        registrar({
            "fecha": datetime.now().isoformat(),
            "origen": actual,
            "destino": destino,
            "resultado": "exitoso",
            "duracion_segundos": duracion
        })

        print("CAMBIO EXITOSO")
        print("Tiempo de operacion:", duracion, "segundos")
        return 0

    except Exception as error:
        print("ERROR:", error)

        # No se intenta revertir si no se conoce el nodo anterior.
        if "actual" in locals() and actual != destino:
            print("Intentando restaurar:", actual)
            try:
                aplicar_cambio(actual)
                verificar_proxy(actual)
                print("Restauracion verificada")
            except Exception as error_reversion:
                print("ERROR DE RESTAURACION:", error_reversion)

        registrar({
            "fecha": datetime.now().isoformat(),
            "destino_solicitado": destino,
            "resultado": "fallido",
            "error": str(error)
        })
        return 1


if __name__ == "__main__":
    sys.exit(main())
