#!/bin/bash

# Script de monitoreo continuo para OFITEC.AI
# Revisa logs, errores y estado del sistema

LOG_FILE="/workspaces/OFITEC.AI/monitoring.log"
ERROR_LOG="/workspaces/OFITEC.AI/errors.log"

echo "$(date): Iniciando monitoreo del sistema OFITEC.AI" >> $LOG_FILE

# Verificar estado de Docker containers
echo "=== Estado de Docker Containers ===" >> $LOG_FILE
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" >> $LOG_FILE 2>&1

# Verificar logs de Odoo en busca de errores
echo "=== Revisando logs de Odoo ===" >> $LOG_FILE
docker logs ofitec-odoo --tail 50 2>&1 | grep -i error >> $ERROR_LOG 2>&1 || echo "No se encontraron errores nuevos en Odoo" >> $LOG_FILE

# Verificar estado de la base de datos
echo "=== Estado de PostgreSQL ===" >> $LOG_FILE
docker exec ofitec-postgres pg_isready -U odoo >> $LOG_FILE 2>&1

# Ejecutar pruebas rápidas
echo "=== Ejecutando pruebas rápidas ===" >> $LOG_FILE
cd /workspaces/OFITEC.AI
python -c "
import sys
sys.path.append('custom_addons')
try:
    import ofitec_core
    print('✓ Módulo ofitec_core: OK')
except ImportError as e:
    print(f'✗ Error en ofitec_core: {e}')
    sys.exit(1)
" >> $LOG_FILE 2>&1

# Verificar sintaxis de archivos CSV y XML
echo "=== Verificación de sintaxis CSV/XML ===" >> $LOG_FILE
find custom_addons/ -name "*.csv" -o -name "*.xml" | while read file; do
    if [[ $file == *.csv ]]; then
        python -c "
import csv
try:
    with open('$file', 'r') as f:
        csv.reader(f)
    print('✓ $file: Sintaxis CSV correcta')
except Exception as e:
    print(f'✗ $file: Error CSV - {e}')
" >> $LOG_FILE 2>&1
    elif [[ $file == *.xml ]]; then
        python -c "
import xml.etree.ElementTree as ET
try:
    ET.parse('$file')
    print('✓ $file: Sintaxis XML correcta')
except Exception as e:
    print(f'✗ $file: Error XML - {e}')
" >> $LOG_FILE 2>&1
    fi
done

# Verificar external IDs en archivos CSV
echo "=== Verificación de External IDs ===" >> $LOG_FILE
find custom_addons/ -name "*.csv" | xargs grep -l "ir.model" | while read file; do
    echo "Revisando external IDs en $file..." >> $LOG_FILE
    grep "ir.model" "$file" >> $LOG_FILE 2>&1
done

# Simular instalación de módulos para detectar errores
echo "=== Simulación de instalación de módulos ===" >> $LOG_FILE
python -c "
import os
import sys
import importlib.util

# Agregar custom_addons al path
sys.path.insert(0, 'custom_addons')

# Lista de módulos OFITEC a verificar
modulos_ofitec = [
    'ofitec_core', 'ofitec_security', 'ofitec_ai_advanced', 
    'ofitec_whatsapp', 'ofitec_project', 'ofitec_qhse',
    'ofitec_visual', 'ofitec_optimizer', 'ofitec_capacity',
    'ofitec_deployment', 'ofitec_backup'
]

for modulo in modulos_ofitec:
    try:
        spec = importlib.util.spec_from_file_location(modulo, f'custom_addons/{modulo}/__init__.py')
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f'✓ {modulo}: Importación exitosa')
        else:
            print(f'✗ {modulo}: No se pudo cargar el módulo')
    except Exception as e:
        print(f'✗ {modulo}: Error de importación - {e}')
" >> $LOG_FILE 2>&1

# Verificar archivos de configuración
echo "=== Verificación de configuración ===" >> $LOG_FILE
if [ -f "docker-compose.yml" ]; then
    echo "✓ docker-compose.yml existe" >> $LOG_FILE
else
    echo "✗ docker-compose.yml no encontrado" >> $ERROR_LOG
fi

# Ejecutar prueba específica de instalación de módulos
echo "=== Ejecutando prueba detallada de módulos ===" >> $LOG_FILE
./test_module_install.sh >> $LOG_FILE 2>&1

# Ejecutar prueba dentro del contenedor Docker
echo "=== Ejecutando prueba en entorno Docker ===" >> $LOG_FILE
./test_docker_modules.sh >> $LOG_FILE 2>&1

# Enviar alerta si hay errores
if [ -s "$ERROR_LOG" ]; then
    echo "=== ALERTA: Se encontraron errores ===" >> $LOG_FILE
    cat $ERROR_LOG >> $LOG_FILE
    # Aquí podrías agregar envío de email o notificación
    # mail -s "Errores en OFITEC.AI" tu-email@example.com < $ERROR_LOG
fi

echo "$(date): Monitoreo completado" >> $LOG_FILE
echo "----------------------------------------" >> $LOG_FILE
