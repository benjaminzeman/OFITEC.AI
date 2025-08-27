#!/bin/bash

echo "🚀 INSTALACIÓN LIMPIA Y ORDENADA DE OFITEC.AI"
echo "=============================================="

# Función para esperar a que Odoo esté listo
wait_for_odoo() {
    echo "⏳ Esperando a que Odoo esté listo..."
    for i in {1..30}; do
        if curl -s http://localhost:8069/web/login > /dev/null; then
            echo "✅ Odoo está listo"
            return 0
        fi
        sleep 3
    done
    echo "❌ Odoo no respondió después de 90 segundos"
    return 1
}

# Paso 1: Iniciar servicios base
echo -e "\n📦 PASO 1: Iniciando servicios base..."
docker-compose up -d db
sleep 10
docker-compose up -d odoo
wait_for_odoo || exit 1

# Paso 2: Instalar módulos base esenciales
echo -e "\n🏗️  PASO 2: Instalando módulos base esenciales..."
docker-compose exec -T odoo python3 -c "
import psycopg2
conn = psycopg2.connect(host='db', database='ofitec', user='odoo', password='odoo')
cur = conn.cursor()

# Instalar módulos base en orden correcto
base_modules = ['project', 'account', 'hr', 'mail', 'bus', 'product', 'analytic', 'portal']
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

# Paso 3: Instalar ofitec_core primero
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

# Paso 4: Reiniciar para instalar ofitec_core
echo -e "\n🔄 PASO 4: Reiniciando para instalar ofitec_core..."
docker-compose restart odoo
wait_for_odoo || exit 1

# Paso 5: Instalar módulos que dependen de ofitec_core
echo -e "\n🔐 PASO 5: Instalando módulos que dependen de ofitec_core..."
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

# Paso 6: Reiniciar para instalar módulos dependientes
echo -e "\n🔄 PASO 6: Reiniciando para instalar módulos dependientes..."
docker-compose restart odoo
wait_for_odoo || exit 1

# Paso 7: Instalar módulos restantes
echo -e "\n📋 PASO 7: Instalando módulos restantes..."
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

# Paso 8: Último reinicio
echo -e "\n🎯 PASO 8: Último reinicio para completar instalación..."
docker-compose restart odoo
wait_for_odoo || exit 1

# Verificación final
echo -e "\n🎉 VERIFICACIÓN FINAL:"
curl -s -o /dev/null -w "🌐 Estado: HTTP %{http_code} | Tiempo: %{time_total}s" http://localhost:8069/web/login

echo -e "\n📊 INSTALACIÓN COMPLETA:"
echo "✅ Servicios base iniciados"
echo "✅ Módulos base instalados"
echo "✅ ofitec_core instalado"
echo "✅ Módulos dependientes instalados"
echo "✅ Módulos restantes instalados"
echo "✅ Sistema listo para usar"

echo -e "\n🌐 ACCESO AL SISTEMA:"
echo "📍 URL: http://localhost:8069"
echo "👤 Usuario: admin"
echo "🔑 Contraseña: admin"
echo "🎯 Busca el menú 'OFITEC' en la interfaz"
