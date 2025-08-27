# OFITEC Next-Best-Action Dashboard

## Descripción

El módulo **Next-Best-Action Dashboard** es un sistema inteligente de recomendaciones que utiliza IA para analizar datos de proyectos y sugerir las mejores acciones a tomar en cada momento. Está diseñado específicamente para proyectos de construcción y gestión de riesgos.

## Características Principales

### 🚀 Dashboard Interactivo
- **Vista en tiempo real** de métricas críticas del proyecto
- **Interfaz moderna** con gradientes y animaciones suaves
- **Responsive design** que funciona en desktop y móvil
- **Actualización automática** de datos cada 5 minutos

### 🤖 Inteligencia Artificial
- **Análisis automático** de riesgos, finanzas y operaciones
- **Generación inteligente** de recomendaciones priorizadas
- **Sistema de confianza** para validar sugerencias de IA
- **Aprendizaje continuo** basado en acciones tomadas

### 📊 Métricas y KPIs
- **Acciones críticas**: Número de acciones con prioridad 1
- **Prioridad alta**: Acciones con prioridad 2
- **Pendientes**: Total de acciones sin completar
- **Completadas hoy**: Acciones finalizadas en el día actual

### 🎯 Sistema de Priorización
- **4 niveles de prioridad**: Crítica (1), Alta (2), Media (3), Baja (4)
- **Puntuaciones de IA**: Confianza, impacto y urgencia
- **Fechas límite** con alertas automáticas
- **Categorización** por tipo de acción

### 📱 Categorías de Acción
- **🎯 Riesgos**: Gestión de seguridad y cumplimiento
- **💰 Financiero**: Control presupuestario y costos
- **⚙️ Operacional**: Eficiencia y procesos
- **🛡️ Calidad**: Estándares y certificaciones
- **📱 Comunicación**: Stakeholders y reporting
- **📋 Planificación**: Cronogramas y recursos

## Funcionalidades

### Análisis de IA
- Ejecuta análisis automático de todos los datos del proyecto
- Identifica patrones y tendencias
- Genera recomendaciones basadas en machine learning
- Actualiza métricas en tiempo real

### Generación de Recomendaciones
- Crea acciones inteligentes basadas en datos
- Prioriza según impacto y urgencia
- Asigna fechas límite automáticas
- Vincula con riesgos y presupuestos específicos

### Gestión de Acciones
- **Estados**: Pendiente, En progreso, Completada, Cancelada
- **Seguimiento**: Historial completo de cambios
- **Asignación**: Usuarios responsables
- **Comentarios**: Chatter integrado

## Instalación y Configuración

### Dependencias
- `ofitec_core`: Módulo base de OFITEC
- `ai_bridge`: Puente de IA para análisis
- `site_management`: Gestión de obras
- `project_risk`: Gestión de riesgos
- `project_financials`: Gestión financiera
- `of_command_palette`: Paleta de comandos

### Configuración
1. Instalar el módulo desde Apps
2. Configurar parámetros del sistema:
   - `ofitec_next_action.dashboard_refresh_interval`: Intervalo de actualización (300s por defecto)
   - `ofitec_next_action.ai_analysis_enabled`: Habilitar análisis de IA (true por defecto)
   - `ofitec_next_action.auto_generate_actions`: Generación automática (false por defecto)

### Permisos
- **Usuario**: Solo lectura
- **Supervisor**: Lectura, escritura, creación
- **Administrador**: Todos los permisos incluyendo eliminación

## Uso del Dashboard

### Acceso
- Menú principal: **Próximas Acciones > Dashboard**
- Página de inicio para usuarios configurados
- URL directa: `/web#action=action_next_action_dashboard`

### Controles Principales
- **🔄 Análisis IA**: Ejecuta análisis completo del proyecto
- **⚡ Generar Recomendaciones**: Crea nuevas acciones inteligentes
- **Ver Detalles**: Abre formulario completo de la acción

### Interpretación de Métricas
- **Rojo (Crítico)**: Requiere atención inmediata
- **Naranja (Alto)**: Importante, atender pronto
- **Azul (Pendiente)**: Normal, en cola de ejecución
- **Verde (Completado)**: Finalizado exitosamente

## Desarrollo

### Estructura de Archivos
```
ofitec_next_action/
├── __manifest__.py              # Configuración del módulo
├── models/
│   └── next_action.py          # Modelo principal
├── views/
│   ├── next_action_views.xml   # Vistas tree/form
│   └── next_action_dashboard.xml # Vista del dashboard
├── data/
│   ├── next_action_data.xml    # Datos de ejemplo
│   └── dashboard_config.xml    # Configuración adicional
├── static/src/
│   ├── js/
│   │   └── next_action.js      # JavaScript del dashboard
│   ├── css/
│   │   └── next_action.css     # Estilos del dashboard
│   └── xml/
│       └── next_action.xml     # Templates OWL
└── security/
    └── ir.model.access.csv     # Permisos de acceso
```

### Componentes OWL
- **NextActionDashboard**: Componente principal del dashboard
- **Métodos principales**:
  - `loadDashboardData()`: Carga datos del servidor
  - `runAIAnalysis()`: Ejecuta análisis de IA
  - `generateRecommendations()`: Genera nuevas acciones
  - `updateMetricsDisplay()`: Actualiza métricas en UI

### API del Modelo
```python
# Obtener datos del dashboard
data = self.get_dashboard_data()

# Ejecutar análisis de IA
result = self.run_ai_analysis()

# Generar recomendaciones
count = self.generate_next_actions()
```

## Personalización

### Agregar Nuevas Categorías
1. Extender el modelo `ofitec.next.action`
2. Agregar opciones al campo `category`
3. Actualizar iconos en `getCategoryIcon()`

### Modificar Algoritmos de IA
1. Extender métodos en `next_action.py`
2. Personalizar `generate_next_actions()`
3. Ajustar pesos de priorización

### Cambiar Apariencia
1. Modificar `next_action.css`
2. Actualizar colores y gradientes
3. Personalizar animaciones

## Solución de Problemas

### Dashboard no carga
- Verificar dependencias instaladas
- Revisar permisos de usuario
- Comprobar configuración de IA

### Análisis de IA falla
- Verificar conexión con `ai_bridge`
- Revisar logs del servidor
- Comprobar configuración de modelos

### Métricas no se actualizan
- Verificar intervalo de actualización
- Comprobar conectividad con base de datos
- Revisar triggers de actualización

## Soporte y Contacto

Para soporte técnico o consultas sobre el módulo, contactar al equipo de desarrollo de OFITEC.

---

**Versión**: 16.0.1.0.0
**Autor**: OFITEC
**Licencia**: LGPL-3
