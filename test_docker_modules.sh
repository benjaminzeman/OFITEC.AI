#!/bin/bash

# Script para probar instalación dentro del contenedor Docker
# Simula el proceso real de instalación de módulos

LOG_FILE="/workspaces/OFITEC.AI/docker_module_test.log"
cd /workspaces/OFITEC.AI

echo "$(date): Iniciando prueba de instalación dentro de Docker" > $LOG_FILE
echo "==========================================" >> $LOG_FILE

# Verificar que Docker esté corriendo
if ! docker ps | grep -q ofitecai-odoo-1; then
    echo "❌ El contenedor ofitecai-odoo-1 no está ejecutándose" >> $LOG_FILE
    echo "Ejecuta: docker-compose up -d" >> $LOG_FILE
    exit 1
fi

echo "✅ Contenedor ofitecai-odoo-1 está ejecutándose" >> $LOG_FILE

# Función para probar instalación de un módulo dentro del contenedor
test_module_in_docker() {
    local module=$1
    echo "=== Probando instalación de $module en Docker ===" >> $LOG_FILE

    # Verificar que el módulo existe
    if [ ! -d "custom_addons/$module" ]; then
        echo "✗ Módulo $module no encontrado" >> $LOG_FILE
        return 1
    fi

    # Ejecutar prueba dentro del contenedor
    docker exec ofitecai-odoo-1 bash -c "
        cd /mnt/extra-addons
        python -c \"
import sys
import os
sys.path.insert(0, '/mnt/extra-addons')
try:
    __import__('$module')
    print('✓ $module: Importación exitosa en Docker')
except Exception as e:
    print(f'✗ $module: Error en Docker - {e}')
    import traceback
    traceback.print_exc()
\"
    " >> $LOG_FILE 2>&1

    # Verificar si el módulo aparece en la lista de módulos disponibles
    echo "Verificando disponibilidad en Odoo..." >> $LOG_FILE
    docker exec ofitecai-odoo-1 python -c "
import odoo
from odoo.modules.registry import Registry
from odoo.tools import config
import logging
logging.getLogger().setLevel(logging.ERROR)

try:
    config.parse_config([])
    registry = Registry(config['db_name'] or 'odoo')
    if '$module' in registry._init_modules:
        print('✓ $module: Disponible en registro de Odoo')
    else:
        print('✗ $module: No encontrado en registro de Odoo')
except Exception as e:
    print(f'⚠ Error al verificar registro: {e}')
" >> $LOG_FILE 2>&1

    echo "✓ Prueba Docker de $module completada" >> $LOG_FILE
    echo "" >> $LOG_FILE
}

# Lista de módulos que existen realmente
modulos_existentes=("ofitec_core" "ofitec_security" "ofitec_ai_advanced" "ofitec_whatsapp" "ofitec_project" "ofitec_qhse" "ofitec_visual" "ofitec_optimizer" "ofitec_capacity" "ofitec_deployment" "ofitec_backup")

for modulo in "${modulos_existentes[@]}"; do
    test_module_in_docker "$modulo"
done

# Verificar estado general del sistema Odoo
echo "=== Estado General del Sistema Odoo ===" >> $LOG_FILE
docker exec ofitecai-odoo-1 python -c "
import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config
import logging
logging.getLogger().setLevel(logging.ERROR)

try:
    config.parse_config([])
    print('✅ Odoo framework cargado correctamente')
    print(f'Versión de Odoo: {odoo.release.version}')
except Exception as e:
    print(f'✗ Error cargando Odoo: {e}')
" >> $LOG_FILE 2>&1

# Verificar módulos instalados
echo "=== Módulos OFITEC Instalados ===" >> $LOG_FILE
docker exec ofitecai-odoo-1 python -c "
from odoo.modules.registry import Registry
from odoo.tools import config
import logging
logging.getLogger().setLevel(logging.ERROR)

try:
    config.parse_config([])
    registry = Registry(config['db_name'] or 'odoo')
    ofitec_modules = [m for m in registry._init_modules if m.startswith('ofitec')]
    print(f'Módulos OFITEC encontrados: {len(ofitec_modules)}')
    for module in sorted(ofitec_modules):
        print(f'  - {module}')
except Exception as e:
    print(f'✗ Error al listar módulos: {e}')
" >> $LOG_FILE 2>&1

echo "==========================================" >> $LOG_FILE
echo "$(date): Prueba Docker completada" >> $LOG_FILE
