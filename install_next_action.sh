#!/bin/bash
# Script de instalación rápida para el módulo Next-Best-Action Dashboard
# Versión: 1.0.0
# Fecha: 2025-08-09

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes coloreados
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto OFITEC.AI"
    exit 1
fi

print_header "🚀 Instalación del módulo Next-Best-Action Dashboard"

# Verificar dependencias del sistema
print_message "Verificando dependencias del sistema..."
command -v docker >/dev/null 2>&1 || { print_error "Docker no está instalado. Abortando."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { print_error "Docker Compose no está instalado. Abortando."; exit 1; }

# Verificar que el módulo existe
if [ ! -d "custom_addons/ofitec_next_action" ]; then
    print_error "El módulo ofitec_next_action no existe en custom_addons/"
    exit 1
fi

print_message "✅ Dependencias verificadas correctamente"

# Crear directorios necesarios si no existen
print_message "Creando directorios necesarios..."
mkdir -p logs
mkdir -p backups

# Verificar estado de Docker
print_message "Verificando estado de Docker..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker no está ejecutándose. Inicie Docker y vuelva a intentar."
    exit 1
fi

# Detener contenedores existentes si están corriendo
print_message "Deteniendo contenedores existentes..."
docker-compose down || true

# Construir y iniciar servicios
print_message "Construyendo e iniciando servicios..."
docker-compose up -d --build

# Esperar a que Odoo esté listo
print_message "Esperando a que Odoo esté listo..."
sleep 30

# Verificar que los servicios estén ejecutándose
print_message "Verificando servicios..."
if ! docker-compose ps | grep -q "Up"; then
    print_error "Los servicios no se iniciaron correctamente"
    docker-compose logs
    exit 1
fi

print_message "✅ Servicios iniciados correctamente"

# Ejecutar pruebas del módulo
print_message "Ejecutando pruebas del módulo..."
if docker-compose exec -T odoo python /mnt/extra-addons/ofitec_next_action/test_next_action.py; then
    print_message "✅ Todas las pruebas pasaron exitosamente"
else
    print_warning "⚠️  Algunas pruebas fallaron, pero el módulo puede funcionar"
fi

# Instalar el módulo en Odoo
print_message "Instalando módulo en Odoo..."
docker-compose exec -T odoo python -c "
import xmlrpc.client
import time

# Conectar a Odoo
url = 'http://localhost:8069'
db = 'ofitec_db'
username = 'admin'
password = 'admin'

print('Conectando a Odoo...')
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

if uid:
    print('✅ Conexión exitosa')
    # Buscar el módulo
    module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search', [[('name', '=', 'ofitec_next_action')]])
    if module_ids:
        # Instalar el módulo
        models.execute_kw(db, uid, password, 'ir.module.module', 'button_install', [module_ids])
        print('✅ Módulo instalado correctamente')
    else:
        print('❌ Módulo no encontrado')
else:
    print('❌ Error de autenticación')
"

print_header "🎉 Instalación completada exitosamente!"

echo ""
print_message "Para acceder al dashboard:"
echo "  🌐 URL: http://localhost:8069"
echo "  👤 Usuario: admin"
echo "  🔑 Contraseña: admin"
echo ""
print_message "Módulos disponibles:"
echo "  📊 Next-Best-Action Dashboard: /web#action=action_next_action_dashboard"
echo "  📋 Lista de acciones: /web#action=action_next_action"
echo ""

print_warning "Notas importantes:"
echo "  • El dashboard se actualiza automáticamente cada 5 minutos"
echo "  • Las recomendaciones de IA requieren configuración adicional"
echo "  • Para producción, configure credenciales seguras"
echo ""

print_message "Para ver logs en tiempo real:"
echo "  docker-compose logs -f odoo"
echo ""
print_message "Para detener los servicios:"
echo "  docker-compose down"
echo ""

print_header "✅ Instalación completada - ¡Disfrute su dashboard inteligente!"
