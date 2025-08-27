# OFITEC WhatsApp Business Integration

## Descripción

La integración de WhatsApp Business API permite enviar notificaciones automáticas y mantener comunicación bidireccional con los usuarios directamente desde el dashboard de Next-Best-Action.

## Características Principales

### 📱 Notificaciones Automáticas
- **Envío automático** de alertas para acciones urgentes (prioridad 1-2)
- **Mensajes inteligentes** con contexto completo de la acción
- **Personalización** por destinatario y proyecto
- **Seguimiento de entregas** y confirmaciones de lectura

### 💬 Comunicación Bidireccional
- **Respuestas inteligentes** a comandos simples:
  - `OK` - Confirmar que se iniciará la acción
  - `COMPLETADO` - Marcar acción como terminada
  - `CANCELAR` - Cancelar la acción
- **Procesamiento automático** de respuestas
- **Actualización en tiempo real** del dashboard

### 📊 Integración con Dashboard
- **Indicadores visuales** de mensajes enviados
- **Botones de acción** para enviar recordatorios manuales
- **Estadísticas de WhatsApp** en el dashboard
- **Historial completo** de conversaciones

### 🔧 Gestión Completa
- **Configuración centralizada** de WhatsApp Business API
- **Múltiples números** de teléfono soportados
- **Modo de pruebas** para desarrollo
- **Webhook seguro** con verificación de firma

## Instalación y Configuración

### Requisitos Previos
- **Cuenta de WhatsApp Business API** activa
- **Phone Number ID** y **Access Token** de Meta/Facebook
- **Servidor público** para webhooks (o ngrok para desarrollo)

### Instalación Automática
```bash
# Desde el directorio raíz del proyecto
./install_whatsapp.sh
```

### Configuración Manual

#### 1. Configurar WhatsApp Business API
1. Ir a **WhatsApp > Configuration**
2. Ingresar:
   - **Phone Number ID**: Tu ID de número de WhatsApp Business
   - **Access Token**: Token de acceso de la API
   - **App Secret**: Secreto de la aplicación
   - **Webhook Verify Token**: Token para verificar webhooks

#### 2. Configurar Webhook
1. En tu cuenta de WhatsApp Business API, configura:
   - **Callback URL**: `https://tudominio.com/webhooks/whatsapp/CONFIG_ID`
   - **Verify Token**: El token configurado en Odoo
2. Selecciona los eventos: `messages`, `message_status`

#### 3. Probar Conexión
1. Usar el botón **"Test Connection"** en la configuración
2. Verificar que aparezca el mensaje de éxito

## Uso del Sistema

### Envío Automático de Notificaciones
Cuando se crea una acción con prioridad 1 o 2:
1. **Se identifica automáticamente** a los destinatarios
2. **Se envía mensaje de WhatsApp** con detalles completos
3. **Se marca la acción** como "WhatsApp enviado"
4. **Aparece indicador visual** en el dashboard

### Respuestas de Usuarios
Los usuarios pueden responder con comandos simples:

#### ✅ Confirmar Acción
```
Usuario: OK
Sistema: ✅ Acción confirmada. Gracias por tu respuesta.
```

#### 🎉 Completar Acción
```
Usuario: COMPLETADO
Sistema: 🎉 Acción completada exitosamente. ¡Excelente trabajo!
```

#### ❌ Cancelar Acción
```
Usuario: CANCELAR
Sistema: ❌ Acción cancelada. Si necesitas ayuda, avísanos.
```

### Dashboard Integration
- **Indicador 📱** muestra si se envió WhatsApp
- **Botón WhatsApp** permite enviar recordatorios manuales
- **Estadísticas** muestran mensajes enviados/recibidos
- **Historial** completo en WhatsApp > Messages

## Configuración Avanzada

### Plantillas de Mensajes
El sistema incluye plantillas predefinidas:
- **urgent_action**: Notificación de acción urgente
- **action_completed**: Confirmación de completación
- **welcome**: Mensaje de bienvenida

### Personalización de Destinatarios
- **Por defecto**: Manager del proyecto y usuario asignado
- **Configurable**: Lista personalizada de destinatarios
- **Condicional**: Solo para acciones urgentes

### Seguridad
- **Verificación de firma** de webhooks
- **Tokens seguros** para autenticación
- **Logs detallados** de todas las operaciones
- **Modo pruebas** para desarrollo seguro

## Desarrollo

### Estructura de Archivos
```
ofitec_whatsapp/
├── __manifest__.py              # Configuración del módulo
├── models/
│   ├── __init__.py             # Inicialización de modelos
│   └── whatsapp.py             # Modelos principales
├── controllers/
│   ├── __init__.py             # Inicialización de controladores
│   └── whatsapp_controller.py  # Controladores web
├── views/
│   └── whatsapp_views.xml      # Vistas de configuración
├── data/
│   └── whatsapp_data.xml       # Datos de ejemplo
└── security/
    └── ir.model.access.csv     # Permisos de acceso
```

### API Endpoints
- **POST** `/api/whatsapp/send_message` - Enviar mensaje
- **POST** `/api/whatsapp/test_connection` - Probar conexión
- **GET** `/api/whatsapp/get_stats` - Obtener estadísticas
- **GET/POST** `/webhooks/whatsapp/<config_id>` - Webhook receptor

### Extensiones
Para extender la funcionalidad:

```python
# En models/whatsapp_integration.py
class NextAction(models.Model):
    _inherit = 'ofitec.next.action'

    def _prepare_whatsapp_message(self):
        # Personalizar mensaje
        message = super()._prepare_whatsapp_message()
        # Agregar lógica personalizada
        return message
```

## Solución de Problemas

### Error de Conexión
- Verificar Phone Number ID y Access Token
- Comprobar que la API esté activa
- Revisar logs de Odoo

### Webhook No Funciona
- Verificar URL del webhook en WhatsApp
- Comprobar que el servidor sea accesible públicamente
- Revisar logs de webhook

### Mensajes No Se Envían
- Verificar configuración activa
- Comprobar destinatarios con números válidos
- Revisar logs de envío

## Estadísticas y Monitoreo

### Métricas Disponibles
- **Mensajes enviados hoy**
- **Mensajes recibidos hoy**
- **Tasa de entrega**
- **Respuestas procesadas**

### Logs
- **Historial completo** en WhatsApp > Messages
- **Logs de sistema** en `/var/log/odoo/odoo.log`
- **Webhook logs** en configuración

## Soporte y Contacto

Para soporte técnico o consultas sobre la integración de WhatsApp, contactar al equipo de desarrollo de OFITEC.

---

**Versión**: 16.0.1.0.0
**Autor**: OFITEC
**Licencia**: LGPL-3
**Dependencias**: WhatsApp Business API, requests, twilio
