#!/bin/bash

# Script para configurar monitoreo automático en entornos Docker
# Versión alternativa que funciona sin cron

LOG_FILE="/workspaces/OFITEC.AI/monitoring_service.log"

echo "$(date): Configurando monitoreo automático para Docker" > $LOG_FILE

# Verificar si ya está ejecutándose
if [ -f "/workspaces/OFITEC.AI/monitor.pid" ]; then
    pid=$(cat /workspaces/OFITEC.AI/monitor.pid)
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "ℹ️ El monitoreo automático ya está ejecutándose (PID: $pid)"
        echo "   Usa './stop_monitoring.sh' para detenerlo"
        echo "   Usa './monitoring_service.sh status' para ver el estado"
        exit 0
    else
        rm -f /workspaces/OFITEC.AI/monitor.pid
    fi
fi

# Verificar que los scripts necesarios existan y sean ejecutables
required_scripts=("monitor_system.sh" "test_module_install.sh" "test_docker_modules.sh")
for script in "${required_scripts[@]}"; do
    if [ ! -x "$script" ]; then
        echo "Corrigiendo permisos de $script..."
        chmod +x "$script"
    fi
done

# Iniciar el servicio de monitoreo
echo "🚀 Iniciando monitoreo automático..."
./monitoring_service.sh start

# Mostrar información de configuración
echo ""
echo "📊 Configuración completada:"
echo "   - Monitoreo automático: cada 4 horas en background"
echo "   - Logs principales: monitoring.log"
echo "   - Logs de errores: errors.log"
echo "   - Logs del servicio: monitoring_service.log"
echo "   - Pruebas de módulos: module_install_test.log"
echo ""
echo "🔧 Comandos disponibles:"
echo "   - Ver estado: ./monitoring_service.sh status"
echo "   - Detener: ./stop_monitoring.sh"
echo "   - Reiniciar: ./monitoring_service.sh restart"
echo "   - Ver logs en tiempo real: tail -f monitoring.log"
