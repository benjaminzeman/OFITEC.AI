# 🔍 Sistema de Monitoreo Automático OFITEC.AI

## 📋 Descripción
Este sistema permite monitorear automáticamente el proyecto OFITEC.AI mientras no estás trabajando, detectando errores comunes que ocurren durante la instalación de módulos.

## 🎯 Problemas que Detecta

### ✅ Errores de Instalación de Módulos
- **Sintaxis incorrecta** en archivos CSV y XML
- **External IDs problemáticos** (como `model_ofitec_core` en lugar de `ir.model_ofitec_core`)
- **Archivos faltantes** (`__init__.py`, `__manifest__.py`)
- **Errores de importación** de módulos Python
- **Problemas de dependencias** entre módulos

### ✅ Errores del Sistema
- **Estado de Docker containers**
- **Logs de errores de Odoo**
- **Estado de PostgreSQL**
- **Configuración de Docker Compose**

## 🚀 Cómo Configurar el Monitoreo Automático

### Opción 1: Configuración Rápida (Recomendada)
```bash
./setup_monitoring.sh
```
- Se ejecuta **cada 4 horas automáticamente** en background
- Funciona en entornos Docker sin necesidad de cron
- Revisa todo el sistema sin intervención
- Genera logs detallados de cualquier problema

### Opción 2: Control Manual del Servicio
```bash
# Ver estado del monitoreo
./monitoring_service.sh status

# Detener el monitoreo
./stop_monitoring.sh

# Reiniciar el monitoreo
./monitoring_service.sh restart
```

## 📊 Archivos de Log Generados

- **`monitoring.log`**: Log principal con estado del sistema
- **`errors.log`**: Solo errores críticos encontrados
- **`module_install_test.log`**: Resultados detallados de pruebas de módulos
- **`monitoring_service.log`**: Log del servicio de monitoreo automático

## 🔧 Ejecutar Monitoreo Manual

### Monitoreo Completo
```bash
./monitor_system.sh
```

### Solo Pruebas de Módulos
```bash
./test_module_install.sh
```

## 📈 Interpretar Resultados

### ✅ Resultados Exitosos
```
✓ Módulo ofitec_core: Importación exitosa
✓ Sintaxis CSV correcta
✓ Sintaxis XML correcta
✅ Todos los módulos pasaron las pruebas básicas
```

### ❌ Problemas Encontrados
```
✗ ofitec_security: Error de importación - No module named 'ofitec_core'
✗ Error CSV: invalid literal for int() with base 10: ''
⚠ ADVERTENCIA: Encontrada referencia 'model_ofitec_core'
❌ Se encontraron problemas que deben corregirse
```

## 🔔 Alertas y Notificaciones

### Configurar Alertas por Email
Edita `monitor_system.sh` y descomenta estas líneas:
```bash
# mail -s "Errores en OFITEC.AI" tu-email@example.com < $ERROR_LOG
```

### Configurar Notificaciones de Slack/Discord
Puedes integrar webhooks para enviar notificaciones automáticas.

## 🔄 Frecuencia de Monitoreo

- **Cada 4 horas**: Cron job automático
- **Inmediato**: Ejecutar manualmente cuando sea necesario
- **Después de cambios**: Siempre después de modificar módulos

## 🛠️ Módulos Monitoreados

- `ofitec_core` ⭐ (Base fundamental)
- `ofitec_security`
- `ofitec_ai_advanced`
- `ofitec_whatsapp`
- `ofitec_project`
- `ofitec_qhse`
- `ofitec_visual`
- `ofitec_optimizer`
- `ofitec_capacity`
- `ofitec_deployment`
- `ofitec_backup`

## 📝 Ejemplo de Output Real

```
=== Estado de Docker Containers ===
ofitecai-odoo-1     Up 11 minutes   0.0.0.0:8069->8069/tcp
ofitecai-db-1       Up 57 minutes   0.0.0.0:5432->5432/tcp

=== Verificación de sintaxis CSV/XML ===
✓ custom_addons/ofitec_security/security/ir.model.access.csv: Sintaxis CSV correcta
✗ custom_addons/ofitec_ai_advanced/static/src/xml/ai_dashboard.xml: Error XML - mismatched tag

=== Ejecutando prueba detallada de módulos ===
✗ ofitec_core: Error de importación - No module named 'odoo'
⚠ ADVERTENCIA: Encontrada referencia 'model_ofitec_core'
```

## 🚨 Solución de Problemas Comunes

### "Permission denied"
```bash
chmod +x *.sh
```

### "No module named 'odoo'"
- El módulo debe probarse dentro del contenedor Docker
- Usar `./test_docker_modules.sh` para pruebas reales

### "Error XML"
- Revisar la línea específica mencionada en el error
- Verificar tags de apertura y cierre

### "External ID no encontrado"
- Cambiar `model_ofitec_core` por `ir.model_ofitec_core`
- Verificar que el módulo base esté instalado

### "crontab: command not found"
- El sistema usa un servicio en background en lugar de cron
- Usar `./monitoring_service.sh` para controlar el monitoreo

---

**💡 Tip:** Revisa los logs regularmente para mantener el sistema saludable. El monitoreo automático te ayudará a detectar problemas antes de que afecten la producción.
