#!/bin/bash

echo "=== GENERADOR DE CARGA PCM ==="
echo "Destino: PCM-Node1"
echo "Duracion maxima: 180 segundos"
echo "Solicitudes concurrentes: 3"

ssh -i ~/.ssh/pcm_node1_ed25519 \
pcmadmin@192.168.56.11 \
"timeout 180 bash -c '
for n in 1 2 3; do
    (
        while true; do
            curl -fsS -o /dev/null \
            \"http://127.0.0.1:5000/compute?iterations=2000000\" \
            || break
        done
    ) &
done
wait
'"
