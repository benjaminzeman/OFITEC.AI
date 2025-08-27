#!/bin/bash

# Script alternativo para configurar monitoreo automático en entornos Docker
# Usa un loop en background en lugar de cron

MONITOR_PID_FILE="/workspaces/OFITEC.AI/monitor.pid"
LOG_FILE="/workspaces/OFITEC.AI/monitoring_service.log"

echo "$(date): Configurando monitoreo automático alternativo" > $LOG_FILE

# Función para verificar si el servicio ya está ejecutándose
is_monitor_running() {
    if [ -f "$MONITOR_PID_FILE" ]; then
        local pid=$(cat "$MONITOR_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Está ejecutándose
        else
            rm -f "$MONITOR_PID_FILE"  # Limpiar PID file obsoleto
            return 1  # No está ejecutándose
        fi
    else
        return 1  # No hay PID file
    fi
}

# Función para detener el monitoreo
stop_monitoring() {
    if is_monitor_running; then
        local pid=$(cat "$MONITOR_PID_FILE")
        echo "Deteniendo monitoreo automático (PID: $pid)..." >> $LOG_FILE
        kill "$pid" 2>/dev/null
        rm -f "$MONITOR_PID_FILE"
        echo "✅ Monitoreo detenido" >> $LOG_FILE
    else
        echo "ℹ️ El monitoreo no está ejecutándose" >> $LOG_FILE
    fi
}

# Función para iniciar el monitoreo en background
start_monitoring() {
    if is_monitor_running; then
        echo "ℹ️ El monitoreo automático ya está ejecutándose" >> $LOG_FILE
        return 0
    fi

    echo "Iniciando monitoreo automático en background..." >> $LOG_FILE

    # Script que se ejecuta en loop
    (
        while true; do
            echo "$(date): Ejecutando monitoreo automático..." >> $LOG_FILE
            cd /workspaces/OFITEC.AI
            ./monitor_system.sh >> $LOG_FILE 2>&1
            echo "$(date): Monitoreo completado, esperando 4 horas..." >> $LOG_FILE
            sleep 14400  # 4 horas = 14400 segundos
        done
    ) &

    local pid=$!
    echo $pid > "$MONITOR_PID_FILE"
    echo "✅ Monitoreo automático iniciado (PID: $pid)" >> $LOG_FILE
    echo "   Se ejecutará cada 4 horas en background"
    echo "   Para detener: ./stop_monitoring.sh"
}

# Función para verificar estado
status_monitoring() {
    if is_monitor_running; then
        local pid=$(cat "$MONITOR_PID_FILE")
        echo "✅ Monitoreo automático activo (PID: $pid)"
        echo "   Última ejecución: $(date -r $LOG_FILE 2>/dev/null || echo 'Desconocida')"
    else
        echo "❌ Monitoreo automático inactivo"
    fi
}

# Procesar argumentos
case "${1:-start}" in
    "start")
        start_monitoring
        ;;
    "stop")
        stop_monitoring
        ;;
    "status")
        status_monitoring
        ;;
    "restart")
        stop_monitoring
        sleep 2
        start_monitoring
        ;;
    *)
        echo "Uso: $0 {start|stop|status|restart}"
        echo "  start  - Iniciar monitoreo automático"
        echo "  stop   - Detener monitoreo automático"
        echo "  status - Ver estado del monitoreo"
        echo "  restart- Reiniciar monitoreo automático"
        exit 1
        ;;
esac

# Mostrar información final
echo ""
echo "📊 Información del servicio:"
echo "   - Log del servicio: $LOG_FILE"
echo "   - Archivo PID: $MONITOR_PID_FILE"
echo "   - Para ver logs en tiempo real: tail -f $LOG_FILE"
echo "   - Para detener: $0 stop"

# Ejecutar una prueba inicial si se está iniciando
if [ "${1:-start}" = "start" ]; then
    echo ""
    echo "Ejecutando prueba inicial..."
    cd /workspaces/OFITEC.AI
    ./monitor_system.sh
fi
