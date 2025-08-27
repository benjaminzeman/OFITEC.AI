#!/bin/bash

# Script para configurar monitoreo automático con cron
# Se ejecutará cada 4 horas para revisar el sistema

CRON_JOB="0 */4 * * * cd /workspaces/OFITEC.AI && ./monitor_system.sh"

# Verificar si el cron job ya existe
if crontab -l | grep -q "monitor_system.sh"; then
    echo "El monitoreo automático ya está configurado"
else
    # Agregar el cron job
    (crontab -l ; echo "$CRON_JOB") | crontab -
    echo "✅ Monitoreo automático configurado para ejecutarse cada 4 horas"
    echo "   Revisa /workspaces/OFITEC.AI/monitoring.log para ver los resultados"
fi

# Mostrar cron jobs actuales
echo ""
echo "Cron jobs actuales:"
crontab -l

# Probar el monitoreo inmediatamente
echo ""
echo "Ejecutando monitoreo inicial..."
cd /workspaces/OFITEC.AI
./monitor_system.sh

echo ""
echo "📊 Configuración completada:"
echo "   - Monitoreo automático: cada 4 horas"
echo "   - Logs principales: monitoring.log"
echo "   - Logs de errores: errors.log"
echo "   - Pruebas de módulos: module_install_test.log"
