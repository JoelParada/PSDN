#!/bin/bash
set -o pipefail

BASE="$HOME/pcm-orquestador"
FECHA=$(date +%Y%m%d_%H%M%S)
LOG="$BASE/resultados/prueba_integral_pcm_$FECHA.log"

echo "=== PRUEBA INTEGRAL PCM V5 ==="
echo "Fecha: $(date)"
echo "Registro: $LOG"
echo "Modo: evaluacion segura, sin conmutacion"

python3 "$BASE/scripts/controlador_pcm_v5.py" 2>&1 | tee "$LOG"

exit "${PIPESTATUS[0]}"
