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

### Opción 2: Configuración Manual
```bash
# Hacer ejecutables los scripts
chmod +x monitor_system.sh
chmod +x test_module_install.sh

# Configurar cron job (cada 4 horas)
crontab -e
# Agregar esta línea:
# 0 */4 * * * cd /workspaces/OFITEC.AI && ./monitor_system.sh
```

## 📊 Archivos de Log Generados

- **`monitoring.log`**: Log principal con estado del sistema
- **`errors.log`**: Solo errores críticos encontrados
- **`module_install_test.log`**: Resultados detallados de pruebas de módulos

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

## 📝 Ejemplo de Output

```
==========================================
Iniciando monitoreo del sistema OFITEC.AI
=== Estado de Docker Containers ===
NAMES               STATUS              PORTS
ofitec-odoo         Up 2 hours          0.0.0.0:8069->8069/tcp
ofitec-postgres     Up 2 hours          5432/tcp

=== Ejecutando prueba detallada de módulos ===
=== Probando instalación de ofitec_core ===
✓ ofitec_core: Importación exitosa
✓ Prueba de ofitec_core completada

✅ Todos los módulos pasaron las pruebas básicas
==========================================
```

## 🚨 Solución de Problemas Comunes

### "Error de importación"
- Verificar dependencias en `__manifest__.py`
- Revisar sintaxis en `__init__.py`

### "Error CSV/XML"
- Verificar formato de archivos
- Revisar caracteres especiales o encoding

### "External ID no encontrado"
- Cambiar `model_ofitec_core` por `ir.model_ofitec_core`
- Verificar que el módulo base esté instalado

---

**💡 Tip:** Revisa los logs regularmente para mantener el sistema saludable. El monitoreo automático te ayudará a detectar problemas antes de que afecten la producción.
