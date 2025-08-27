#!/bin/bash
# Script de instalación para la integración de WhatsApp
# Versión: 1.0.0
# Fecha: 2025-08-27

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

print_header "📱 Instalación de WhatsApp Integration"

# Verificar dependencias del sistema
print_message "Verificando dependencias del sistema..."
command -v docker >/dev/null 2>&1 || { print_error "Docker no está instalado. Abortando."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { print_error "Docker Compose no está instalado. Abortando."; exit 1; }

# Verificar que los módulos existen
if [ ! -d "custom_addons/ofitec_whatsapp" ]; then
    print_error "El módulo ofitec_whatsapp no existe en custom_addons/"
    exit 1
fi

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

# Instalar los módulos en Odoo
print_message "Instalando módulos en Odoo..."
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

    # Instalar módulo de WhatsApp
    whatsapp_module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search', [[('name', '=', 'ofitec_whatsapp')]])
    if whatsapp_module_ids:
        models.execute_kw(db, uid, password, 'ir.module.module', 'button_install', [whatsapp_module_ids])
        print('✅ Módulo WhatsApp instalado correctamente')
    else:
        print('❌ Módulo WhatsApp no encontrado')

    # Verificar que next_action esté actualizado
    next_action_module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search', [[('name', '=', 'ofitec_next_action')]])
    if next_action_module_ids:
        # Si está instalado, actualizarlo
        models.execute_kw(db, uid, password, 'ir.module.module', 'button_upgrade', [next_action_module_ids])
        print('✅ Módulo Next Action actualizado correctamente')
    else:
        print('❌ Módulo Next Action no encontrado')

else:
    print('❌ Error de autenticación')
"

print_header "🎉 ¡WhatsApp Integration instalado exitosamente!"

echo ""
print_message "Para configurar WhatsApp:"
echo "  🌐 URL: http://localhost:8069/web#action=action_whatsapp_config"
echo "  👤 Usuario: admin"
echo "  🔑 Contraseña: admin"
echo ""

print_message "Pasos de configuración:"
echo "  1. 📱 Ir a WhatsApp > Configuration"
echo "  2. 🔧 Configurar Phone Number ID y Access Token"
echo "  3. 🔒 Configurar Webhook Verify Token"
echo "  4. 🧪 Probar la conexión"
echo "  5. 📊 Ver estadísticas en el dashboard"
echo ""

print_warning "Notas importantes:"
echo "  • Necesitas una cuenta de WhatsApp Business API"
echo "  • Configura el webhook URL en tu cuenta de WhatsApp"
echo "  • Las notificaciones automáticas se activan para acciones urgentes"
echo "  • Los usuarios pueden responder con comandos simples (OK, COMPLETADO, CANCELAR)"
echo ""

print_message "URLs importantes:"
echo "  📊 Dashboard: /web#action=action_next_action_dashboard"
echo "  📱 WhatsApp Config: /web#action=action_whatsapp_config"
echo "  💬 WhatsApp Messages: /web#action=action_whatsapp_message"
echo ""

print_message "Comandos de respuesta disponibles:"
echo "  ✅ OK - Confirmar acción"
echo "  🎉 COMPLETADO - Marcar como completada"
echo "  ❌ CANCELAR - Cancelar acción"
echo ""

print_header "✅ ¡Configuración completada!"

echo ""
print_message "Para ver logs en tiempo real:"
echo "  docker-compose logs -f odoo"
echo ""
print_message "Para detener los servicios:"
echo "  docker-compose down"
echo ""

print_header "🚀 ¡Disfruta tu integración con WhatsApp!"
