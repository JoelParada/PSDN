#!/usr/bin/env python3

import subprocess
from datetime import datetime

NODOS = {
    "PCM-Node1 (ORIGEN)": {
        "ip": "192.168.56.11",
        "clave": "/home/pcmadmin/.ssh/pcm_node1_ed25519"
    },
    "PCM-Node3 (DESTINO)": {
        "ip": "192.168.56.13",
        "clave": "/home/pcmadmin/.ssh/pcm_node3_ed25519"
    }
}

def ejecutar_remoto(ip, clave, comando):
    resultado = subprocess.run(
        [
            "ssh",
            "-i", clave,
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            "pcmadmin@" + ip,
            comando
        ],
        capture_output=True,
        text=True,
        timeout=15
    )

    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip())

    return resultado.stdout.strip()


print("=== DIAGNOSTICO DEL ORQUESTADOR PCM ===")
print("Fecha:", datetime.now().isoformat(timespec="seconds"))

todos_correctos = True

for nombre, datos in NODOS.items():
    print("\n---", nombre, "---")

    ip = datos["ip"]
    clave = datos["clave"]

    try:
        hostname = ejecutar_remoto(ip, clave, "hostname")
        print("SSH: OK -", hostname)

        docker = ejecutar_remoto(
            ip, clave, "docker info --format '{{.ServerVersion}}'"
        )
        print("Docker: OK - version", docker)

        estado = ejecutar_remoto(
            ip, clave,
            "docker inspect pcm-flask-app "
            "--format '{{.State.Status}}'"
        )
        print("Flask:", estado)

        imagen = ejecutar_remoto(
            ip, clave,
            "docker image inspect pcm-flask:v1 "
            "--format '{{.Id}}'"
        )
        print("Imagen:", imagen)

        if estado != "running":
            todos_correctos = False
            print("ADVERTENCIA: Flask no esta ejecutandose")

    except (RuntimeError, subprocess.TimeoutExpired) as error:
        todos_correctos = False
        print("ERROR:", error)

print("\n=== RESULTADO GENERAL ===")

if todos_correctos:
    print("OK: Ambos nodos estan preparados")
else:
    print("ADVERTENCIA: Revisar los errores anteriores")
