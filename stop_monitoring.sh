#!/bin/bash

# Script simple para detener el monitoreo automático
cd /workspaces/OFITEC.AI

if [ -f "monitor.pid" ]; then
    pid=$(cat monitor.pid)
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Deteniendo monitoreo automático (PID: $pid)..."
        kill "$pid"
        echo "✅ Monitoreo detenido"
    else
        echo "El proceso de monitoreo no está ejecutándose"
    fi
    rm -f monitor.pid
else
    echo "No hay monitoreo automático ejecutándose"
fi
