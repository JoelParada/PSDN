#!/bin/bash
set -u

BASE="$HOME/pcm-orquestador"
SCRIPTS="$BASE/scripts"
RESULTADOS="$BASE/resultados"
FECHA=$(date +%Y%m%d_%H%M%S)
LOG="$RESULTADOS/autonoma_lstm_v5_$FECHA.log"

mkdir -p "$RESULTADOS"

echo "=== PRUEBA AUTONOMA PCM CON LSTM REAL ===" | tee "$LOG"

echo "Verificando nodo inicial..." | tee -a "$LOG"

if ! python3 "$SCRIPTS/detectar_nodo_activo.py" | grep -q "pcm-node1"; then
    echo "ERROR: PCM-Node1 no esta activo" | tee -a "$LOG"
    exit 1
fi

echo "Iniciando carga real..." | tee -a "$LOG"

bash "$SCRIPTS/generar_carga_pcm.sh" >> "$LOG" 2>&1 &
PID_CARGA=$!

cleanup() {
    if kill -0 "$PID_CARGA" 2>/dev/null; then
        kill "$PID_CARGA" 2>/dev/null || true
    fi
}
trap cleanup EXIT

sleep 25

echo "Ejecutando controlador con LSTM V5 real..." | tee -a "$LOG"

python3 "$SCRIPTS/controlador_pcm_v5.py" \
    --autorizar-conmutacion 2>&1 | tee -a "$LOG"

RESULTADO=${PIPESTATUS[0]}

echo "Verificando nodo final..." | tee -a "$LOG"

python3 "$SCRIPTS/detectar_nodo_activo.py" | tee -a "$LOG"

echo "Archivo de evidencia: $LOG"

exit "$RESULTADO"
