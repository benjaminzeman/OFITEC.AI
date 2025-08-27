#!/bin/bash

# Script específico para probar instalación de módulos OFITEC
# Detecta los mismos errores que vimos durante la instalación

LOG_FILE="/workspaces/OFITEC.AI/module_install_test.log"
cd /workspaces/OFITEC.AI

echo "$(date): Iniciando prueba de instalación de módulos OFITEC" > $LOG_FILE
echo "==========================================" >> $LOG_FILE

# Función para probar instalación de un módulo
test_module_install() {
    local module=$1
    echo "=== Probando instalación de $module ===" >> $LOG_FILE

    # Verificar que el módulo existe
    if [ ! -d "custom_addons/$module" ]; then
        echo "✗ Módulo $module no encontrado en custom_addons/" >> $LOG_FILE
        return 1
    fi

    # Verificar __init__.py
    if [ ! -f "custom_addons/$module/__init__.py" ]; then
        echo "✗ $module: Falta archivo __init__.py" >> $LOG_FILE
        return 1
    fi

    # Verificar __manifest__.py
    if [ ! -f "custom_addons/$module/__manifest__.py" ]; then
        echo "✗ $module: Falta archivo __manifest__.py" >> $LOG_FILE
        return 1
    fi

    # Probar importación del módulo
    python -c "
import sys
sys.path.insert(0, 'custom_addons')
try:
    import $module
    print('✓ $module: Importación exitosa')
except Exception as e:
    print(f'✗ $module: Error de importación - {e}')
    import traceback
    traceback.print_exc()
" >> $LOG_FILE 2>&1

    # Verificar archivos de seguridad
    if [ -d "custom_addons/$module/security" ]; then
        echo "Revisando archivos de seguridad..." >> $LOG_FILE
        find "custom_addons/$module/security" -name "*.csv" -o -name "*.xml" | while read file; do
            echo "  Verificando $file..." >> $LOG_FILE

            # Verificar sintaxis CSV
            if [[ $file == *.csv ]]; then
                python -c "
import csv
try:
    with open('$file', 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Leer headers
        for row in reader:
            pass  # Procesar filas
    print('  ✓ Sintaxis CSV correcta')
except Exception as e:
    print(f'  ✗ Error CSV: {e}')
" >> $LOG_FILE 2>&1
            fi

            # Verificar sintaxis XML
            if [[ $file == *.xml ]]; then
                python -c "
import xml.etree.ElementTree as ET
try:
    ET.parse('$file')
    print('  ✓ Sintaxis XML correcta')
except Exception as e:
    print(f'  ✗ Error XML: {e}')
" >> $LOG_FILE 2>&1
            fi
        done
    fi

    # Verificar external IDs específicos que causaron problemas
    echo "Buscando external IDs problemáticos..." >> $LOG_FILE
    find "custom_addons/$module" -name "*.csv" -o -name "*.xml" | xargs grep -l "ir.model" 2>/dev/null | while read file; do
        echo "  Revisando external IDs en $file:" >> $LOG_FILE
        grep "ir.model" "$file" >> $LOG_FILE 2>&1

        # Verificar si hay referencias problemáticas (no precedidas por 'ir.')
        if grep -q "^[^,]*model_ofitec_core" "$file" || grep -q ",model_ofitec_core" "$file"; then
            echo "  ⚠ ADVERTENCIA: Encontrada referencia 'model_ofitec_core' en $file" >> $LOG_FILE
            echo "    Debería ser 'ir.model_ofitec_core'" >> $LOG_FILE
        fi
    done

    echo "✓ Prueba de $module completada" >> $LOG_FILE
    echo "" >> $LOG_FILE
}

# Lista de módulos a probar
modulos=("ofitec_core" "ofitec_security" "ofitec_ai_advanced" "ofitec_whatsapp" "ofitec_project" "ofitec_qhse" "ofitec_visual" "ofitec_optimizer" "ofitec_capacity" "ofitec_deployment" "ofitec_backup")

for modulo in "${modulos[@]}"; do
    test_module_install "$modulo"
done

# Resumen final
echo "==========================================" >> $LOG_FILE
echo "RESUMEN DE PRUEBAS:" >> $LOG_FILE
echo "- Errores de sintaxis encontrados: $(grep -c "✗.*Error" $LOG_FILE)" >> $LOG_FILE
echo "- Advertencias de external IDs: $(grep -c "⚠ ADVERTENCIA" $LOG_FILE)" >> $LOG_FILE
echo "- Módulos con problemas: $(grep -c "✗.*:" $LOG_FILE)" >> $LOG_FILE

if grep -q "✗\|⚠" $LOG_FILE; then
    echo "❌ Se encontraron problemas que deben corregirse" >> $LOG_FILE
else
    echo "✅ Todos los módulos pasaron las pruebas básicas" >> $LOG_FILE
fi

echo "$(date): Prueba de instalación completada" >> $LOG_FILE
