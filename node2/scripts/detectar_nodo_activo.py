#!/usr/bin/env python3

import re
import sys
from pathlib import Path

ARCHIVO = Path("/etc/nginx/conf.d/pcm-upstream.conf")

NODOS = {
    ("192.168.56.11", 5000): "pcm-node1",
    ("192.168.56.13", 5001): "pcm-node3",
}


def obtener_nodo_activo():
    contenido = ARCHIVO.read_text(encoding="utf-8")

    servidores = re.findall(
        r"^\s*server\s+(\d+\.\d+\.\d+\.\d+):(\d+)\s*;",
        contenido,
        flags=re.MULTILINE
    )

    if len(servidores) != 1:
        raise RuntimeError(
            "Se esperaba exactamente un servidor upstream"
        )

    ip, puerto = servidores[0]
    nodo = NODOS.get((ip, int(puerto)))

    if nodo is None:
        raise RuntimeError(
            "Destino no reconocido: {}:{}".format(ip, puerto)
        )

    return nodo


def main():
    print("=== DETECCION DEL NODO ACTIVO ===")

    try:
        nodo = obtener_nodo_activo()
        print("Nodo activo configurado:", nodo)
        print("Deteccion completada correctamente")
        return 0

    except Exception as error:
        print("ERROR:", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
