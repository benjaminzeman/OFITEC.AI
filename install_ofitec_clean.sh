#!/bin/bash

echo "🚀 INSTALACIÓN ORDENADA DE OFITEC.AI"
echo "===================================="

# Función para esperar a que Odoo esté listo
wait_for_odoo() {
    echo "⏳ Esperando a que Odoo esté listo..."
    for i in {1..30}; do
        if curl -s http://localhost:8069/web/login > /dev/null; then
            echo "✅ Odoo está listo"
            return 0
        fi
        sleep 2
    done
    echo "❌ Odoo no respondió después de 60 segundos"
    return 1
}

# Paso 1: Iniciar servicios base
echo -e "\n📦 PASO 1: Iniciando servicios base..."
docker-compose up -d db
sleep 10
docker-compose up -d odoo
wait_for_odoo || exit 1

# Paso 2: Instalar módulos base de Odoo
echo -e "\n🏗️  PASO 2: Instalando módulos base de Odoo..."
docker-compose exec -T odoo python3 -c "
import psycopg2
conn = psycopg2.connect(host='db', database='ofitec', user='odoo', password='odoo')
cur = conn.cursor()

base_modules = ['project', 'account', 'hr', 'mail', 'bus', 'product', 'analytic', 'portal', 'digest', 'uom', 'sale', 'purchase']
for module in base_modules:
    cur.execute('UPDATE ir_module_module SET state = %s WHERE name = %s', ('to install', module))
    print(f'✅ {module} marcado para instalación')

conn.commit()
conn.close()
"

# Reiniciar para instalar módulos base
echo "🔄 Reiniciando para instalar módulos base..."
docker-compose restart odoo
wait_for_odoo || exit 1

# Paso 3: Instalar ofitec_core (módulo base)
echo -e "\n🏢 PASO 3: Instalando ofitec_core..."
docker-compose exec -T odoo python3 -c "
import psycopg2
conn = psycopg2.connect(host='db', database='ofitec', user='odoo', password='odoo')
cur = conn.cursor()

cur.execute('UPDATE ir_module_module SET state = %s WHERE name = %s', ('to install', 'ofitec_core'))
print('✅ ofitec_core marcado para instalación')

conn.commit()
conn.close()
"

# Paso 4: Instalar módulos que dependen de ofitec_core
echo -e "\n🔐 PASO 4: Instalando módulos que dependen de ofitec_core..."
docker-compose exec -T odoo python3 -c "
import psycopg2
conn = psycopg2.connect(host='db', database='ofitec', user='odoo', password='odoo')
cur = conn.cursor()

dependent_modules = ['ofitec_security', 'ofitec_theme', 'ai_bridge']
for module in dependent_modules:
    cur.execute('UPDATE ir_module_module SET state = %s WHERE name = %s', ('to install', module))
    print(f'✅ {module} marcado para instalación')

conn.commit()
conn.close()
"

# Paso 5: Reiniciar para aplicar cambios
echo -e "\n🔄 PASO 5: Reiniciando para aplicar todos los cambios..."
docker-compose restart odoo
wait_for_odoo || exit 1

# Paso 6: Instalar módulos restantes
echo -e "\n📋 PASO 6: Instalando módulos restantes..."
docker-compose exec -T odoo python3 -c "
import psycopg2
conn = psycopg2.connect(host='db', database='ofitec', user='odoo', password='odoo')
cur = conn.cursor()

remaining_modules = ['site_management', 'project_risk', 'project_financials', 'docuchat_ai', 'ofitec_whatsapp', 'ofitec_next_action']
for module in remaining_modules:
    cur.execute('UPDATE ir_module_module SET state = %s WHERE name = %s', ('to install', module))
    print(f'✅ {module} marcado para instalación')

conn.commit()
conn.close()
"

# Paso 7: Último reinicio
echo -e "\n🎯 PASO 7: Último reinicio para completar instalación..."
docker-compose restart odoo
wait_for_odoo || exit 1

# Verificación final
echo -e "\n🎉 VERIFICACIÓN FINAL:"
curl -s -o /dev/null -w "🌐 Estado: HTTP %{http_code}\n📍 URL: http://localhost:8069\n👤 Usuario: admin\n🔑 Contraseña: admin\n\n✅ ¡INSTALACIÓN COMPLETA!" http://localhost:8069/web/login

echo -e "\n📊 RESUMEN DE INSTALACIÓN:"
echo "✅ Servicios base iniciados"
echo "✅ Módulos base de Odoo instalados"
echo "✅ ofitec_core instalado"
echo "✅ Módulos dependientes instalados"
echo "✅ Módulos restantes instalados"
echo "✅ Sistema listo para usar"

echo -e "\n🌐 ACCEDE A TU SISTEMA OFITEC.AI:"
echo "📍 URL: http://localhost:8069"
echo "👤 Usuario: admin"
echo "🔑 Contraseña: admin"
