from flask import Flask, jsonify, request
import os
import time
import socket

app = Flask(__name__)

# Identifica el contenedor que ejecuta la aplicacion
NODE_NAME = os.environ.get("NODE_NAME", socket.gethostname())


# Ruta principal: comprueba que la aplicacion funciona
@app.route("/")
def inicio():
    return jsonify({
        "mensaje": "Predictive Container Migration",
        "estado": "funcionando",
        "nodo": NODE_NAME
    })


# Ruta para comprobar la disponibilidad del servicio
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "node": NODE_NAME
    })


# Ruta para generar trabajo real de CPU
@app.route("/compute")
def compute():
    inicio = time.perf_counter()

    # Cantidad de operaciones solicitadas
    iterations = request.args.get(
        "iterations", default=100000, type=int
    )

    # Limita el trabajo para evitar solicitudes excesivas
    iterations = max(1, min(iterations, 2000000))

    resultado = 0

    for i in range(iterations):
        resultado += (i * i) % 97

    duracion = time.perf_counter() - inicio

    return jsonify({
        "node": NODE_NAME,
        "iterations": iterations,
        "resultado": resultado,
        "duracion_segundos": round(duracion, 6)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
