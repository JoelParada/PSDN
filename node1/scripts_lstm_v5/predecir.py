import csv
from pathlib import Path

import numpy as np
import tensorflow as tf

BASE = Path(__file__).resolve().parents[1]
DATOS = BASE / "evaluacion_lstm_v5"
MODELO = BASE / "modelo_lstm_v5"

parametros = np.load(
    MODELO / "parametros_normalizacion_pcm_v5.npz"
)

minimo = float(parametros["minimo"])
rango = float(parametros["rango"])

modelo = tf.keras.models.load_model(
    MODELO / "cpu_forecaster_pcm_v5.keras",
    compile=False
)

salida = DATOS / "predicciones_nuevas_v5.csv"
resultados = []

for escenario in ["growth", "spike"]:
    archivos = sorted(DATOS.glob(f"{escenario}_v5_*.csv"))

    if len(archivos) != 1:
        raise RuntimeError(
            f"Se esperaba un CSV para {escenario}: {archivos}"
        )

    with archivos[0].open(newline="") as f:
        filas = list(csv.DictReader(f))

    valores = [float(f["cpu_pct"]) for f in filas]

    for i in range(10, len(valores)):
        ventana = np.array(
            valores[i-10:i], dtype=np.float32
        )

        X = ((ventana - minimo) / rango).reshape(1, 10, 1)

        pred = float(
            modelo.predict(X, verbose=0)[0][0] * rango + minimo
        )

        real = valores[i]
        baseline = valores[i-1]

        resultados.append({
            "escenario": escenario,
            "timestamp": filas[i]["timestamp"],
            "cpu_real": real,
            "cpu_predicha_lstm": pred,
            "cpu_predicha_baseline": baseline
        })

        print(
            f"{escenario.upper()} | "
            f"Real={real:.2f}% | "
            f"LSTM={pred:.2f}% | "
            f"Baseline={baseline:.2f}%",
            flush=True
        )

with salida.open("w", newline="") as f:
    escritor = csv.DictWriter(
        f,
        fieldnames=[
            "escenario",
            "timestamp",
            "cpu_real",
            "cpu_predicha_lstm",
            "cpu_predicha_baseline"
        ]
    )
    escritor.writeheader()
    escritor.writerows(resultados)

print()
print("=== RESULTADOS POR ESCENARIO ===")

for escenario in ["growth", "spike"]:
    filas = [r for r in resultados if r["escenario"] == escenario]

    real = np.array([r["cpu_real"] for r in filas])
    lstm = np.array([r["cpu_predicha_lstm"] for r in filas])
    base = np.array([r["cpu_predicha_baseline"] for r in filas])

    print(
        f"{escenario.upper()}: {len(filas)} predicciones | "
        f"MAE LSTM={np.mean(np.abs(real-lstm)):.4f} | "
        f"MAE Baseline={np.mean(np.abs(real-base)):.4f}"
    )

print("CSV GENERADO:", salida)
