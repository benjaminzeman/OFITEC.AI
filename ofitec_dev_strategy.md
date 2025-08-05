# Estrategia Técnica OFITEC (Arquitectura y Detalle)

## Diagrama General
![Diagrama de Módulos y Dependencias](attachment://ofitec_modules_dependencies_diagram.png)
_Este diagrama visual complementa el contenido y no reemplaza las secciones._

## 1. Arquitectura General
- Backend: Odoo 16 (Python 3.8+, PostgreSQL 12+)
- Frontend: OWL, SCSS modular
- Infraestructura: Docker Compose, CI/CD con GitHub Actions
- Servicios externos: Google Drive API, WhatsApp Cloud API, IA (LangChain + Transformers)
- Mensajería: Redis/RabbitMQ

## 2. Módulos y Relaciones
- ofitec_core: API central y base de datos
- ofitec_theme: UI conectada a ofitec_core
- ofitec_security: Roles, permisos y control de acceso
- site_management: Relacionado con project_documents y ai_bridge
- project_financials: Vinculado a site_management y account
- project_risk: Integrado con IA
- docuchat_ai: Conecta documentos y Drive
- ai_bridge: Motor de predicciones

### Dependencias
- site_management depende de ofitec_core y ofitec_security
- project_financials depende de site_management y account
- project_risk depende de ai_bridge y site_management
- docuchat_ai depende de documents y Drive

## 3. Roles y Permisos
- Administrador: Acceso total
- Gerente General: Dashboards, riesgos, finanzas
- Project Manager: Control de obra, documentos
- Supervisor: Reportes diarios, inspecciones
- Estudio de Propuestas: Consulta documentos y presupuestos
- Permisos avanzados por proyecto

## 4. Flujos Principales
1. Avances → IA valida → Dashboard
2. Documentos → Drive Sync → DocuChat indexa
3. Presupuestos → Financials → IA proyecta
4. Riesgos → AI Bridge analiza → Alertas
5. WhatsApp → Registro y análisis de sentimiento

## 5. Integración de IA con Workflows
- Validación automática de avances
- Recomendaciones de reasignación
- Alertas de desviaciones por WhatsApp

## 6. Análisis de Sentimiento
- Procesamiento con Transformers
- Métricas de estado de equipo
- Alertas automáticas por patrones negativos

## 7. Flujo de Aprobación de Documentos
- mail.activity para flujos de aprobación
- Reglas por rol (PM planos, Gerencia presupuestos)

## 8. Monitoreo y Logs

### Paneles Recomendados en Grafana
1. **Panel de Rendimiento del Sistema:**
   - Tiempo de respuesta promedio de Odoo.
   - Jobs en cola (`queue_job`).
   - Uso de CPU y memoria.

2. **Panel de Estado de Proyectos:**
   - Avances registrados en `site_management`.
   - Presupuestos vs. gastos en `project_financials`.
   - Riesgos activos de `project_risk`.

3. **Panel de Integraciones:**
   - Tareas de sincronización con Google Drive.
   - Mensajes procesados de WhatsApp.
   - Consultas realizadas en `docuchat_ai`.

4. **Panel de Calidad del Código:**
   - Cobertura de pruebas (`pytest-cov`).
   - Resultados de linting.

_Estos paneles permiten un monitoreo completo tanto de la infraestructura como de la operación de OFITEC._

### Diagrama de Monitoreo y Métricas

### Diagrama de Monitoreo y Métricas
```python
from graphviz import Digraph

monitoring_flow = Digraph('OfitecMonitoringFlow', format='png')

monitoring_flow.node('Odoo', 'Odoo')
monitoring_flow.node('prometheus_exporter', 'Prometheus Exporter')
monitoring_flow.node('Prometheus', 'Prometheus')
monitoring_flow.node('Grafana', 'Grafana')
monitoring_flow.node('ELK', 'ELK Stack')

monitoring_flow.edge('Odoo', 'prometheus_exporter', label='Expone métricas')
monitoring_flow.edge('prometheus_exporter', 'Prometheus', label='Recolección de métricas')
monitoring_flow.edge('Prometheus', 'Grafana', label='Visualización de métricas')
monitoring_flow.edge('Odoo', 'ELK', label='Envío de logs')

print(monitoring_flow.source)
```
_Este script genera un diagrama de monitoreo que muestra cómo las métricas y logs de Odoo son recolectados y visualizados._

### Flujos de Datos de Monitoreo y Métricas
1. Prometheus recolecta métricas de Odoo usando `odoo-prometheus-exporter`.
2. Las métricas incluyen tiempos de respuesta, trabajos en cola y errores.
3. Grafana consulta Prometheus para mostrar paneles de rendimiento.
4. ELK Stack procesa logs generados por Odoo y los muestra para auditoría.
5. Alertas configuradas en Grafana notifican al equipo de TI en caso de anomalías.


### Flujos de Datos de Monitoreo y Métricas
1. Prometheus recolecta métricas de Odoo usando `odoo-prometheus-exporter`.
2. Las métricas incluyen tiempos de respuesta, trabajos en cola y errores.
3. Grafana consulta Prometheus para mostrar paneles de rendimiento.
4. ELK Stack procesa logs generados por Odoo y los muestra para auditoría.
5. Alertas configuradas en Grafana notifican al equipo de TI en caso de anomalías.

- Prometheus para métricas
- Grafana para dashboards
- ELK Stack para auditoría

### Configuración Prometheus
```yaml
scrape_configs:
  - job_name: 'odoo'
    static_configs:
      - targets: ['localhost:8069']
```

## 9. Indexación DocuChat
- Preprocesamiento PDF/DWG
- Embeddings PostgreSQL
- Indexación incremental

## 10. Estructura de Carpetas y Archivos
- custom_addons/ofitec_core/models/core_model.py
- custom_addons/ofitec_core/controllers/main.py
- custom_addons/ofitec_theme/static/css/ofitec_base.scss
- custom_addons/ofitec_security/security/ir.model.access.csv
- custom_addons/site_management/models/daily_report.py
- custom_addons/project_financials/models/project_budget.py
- custom_addons/project_risk/models/risk_record.py
- custom_addons/docuchat_ai/services/vector_indexer.py

## 11. Integraciones API
### Google Drive
```python
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def upload_file(file_path, folder_id):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    file = drive.CreateFile({'parents': [{'id': folder_id}]})
    file.SetContentFile(file_path)
    file.Upload()
```

### WhatsApp
```python
import requests

def send_whatsapp_message(phone, message):
    url = 'https://graph.facebook.com/v16.0/YOUR_PHONE_ID/messages'
    headers = {'Authorization': 'Bearer YOUR_ACCESS_TOKEN', 'Content-Type': 'application/json'}
    data = {
        'messaging_product': 'whatsapp',
        'to': phone,
        'type': 'text',
        'text': {'body': message}
    }
    return requests.post(url, headers=headers, json=data).json()
```

## 12. Cron Jobs y Colas
### Cron XML
```xml
<odoo>
  <data noupdate="1">
    <record id="ir_cron_sync_drive" model="ir.cron">
      <field name="name">Sync Google Drive</field>
      <field name="model_id" ref="model_ofitec_drive_service"/>
      <field name="state">code</field>
      <field name="code">model.sync_drive_files()</field>
      <field name="interval_number">10</field>
      <field name="interval_type">minutes</field>
    </record>
  </data>
</odoo>
```

### Colas
```python
from odoo.addons.queue_job.job import job

class DriveService(models.Model):
    _name = 'ofitec.drive.service'

    @job
    def sync_drive_files(self):
        # Lógica para sincronización de archivos
        pass
```

## 13. Notificaciones en Tiempo Real
### Redis
```python
import redis
redis_client = redis.Redis(host='localhost', port=6379)
redis_client.publish('ofitec_notifications', 'Nuevo reporte diario registrado')
```

### Odoo bus.bus
```python
self.env['bus.bus']._sendone('project_updates', 'message', {
    'title': 'Nuevo avance registrado',
    'body': 'El proyecto X tiene un 5% de progreso adicional'
})
```

## 14. Ejemplos de Código
- Modelos, controladores y servicios IA
- Integración Google Drive y WhatsApp API
- Cron jobs y colas
- Notificaciones con bus.bus
- Análisis de sentimiento con Transformers

## 15. Monitoreo y Pruebas
- Prometheus y Exporter
- Dashboards Grafana
- Pytest unitario e integración
- ELK Stack
- Codespaces con Docker

## 16. Módulos Odoo, OCA, GitHub y Propios
- Odoo: project, hr, account, stock, mail, documents, bus
- OCA: queue_job, project_task_dependency, contract
- GitHub: whatsapp-connector, prometheus-exporter
- Propios: ofitec_core, ofitec_theme, ofitec_security, site_management, project_financials, project_risk, docuchat_ai, ai_bridge

## 17. Dependencias y Orden
1. Módulos base de Odoo
2. Módulos OCA
3. ofitec_core y ofitec_security
4. site_management
5. project_financials
6. project_risk y ai_bridge
7. docuchat_ai

## 18. Próximos Pasos
- Integrar métricas IA
- Alertas automáticas Grafana
- Pruebas de carga
- IoT y Marketplace de módulos

## 19. Descripción y Justificación de Módulos

## Ejemplo de devcontainer.json para Codespaces
```json
{
  "name": "OFITEC Development Container",
  "image": "mcr.microsoft.com/vscode/devcontainers/python:3.9",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "postCreateCommand": "pip install -r requirements.txt",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-azuretools.vscode-docker",
        "mhutchie.git-graph",
        "batisteo.vscode-django",
        "ms-vscode-remote.remote-containers"
      ]
    }
  },
  "remoteUser": "vscode",
  "mounts": [
    "source=${localWorkspaceFolder}/custom_addons,target=/workspace/custom_addons,type=bind"
  ],
  "dockerComposeFile": [
    "../docker-compose.yml"
  ],
  "service": "odoo",
  "workspaceFolder": "/workspace"
}
```
_Este archivo configura Codespaces para trabajar con Odoo, Docker y las extensiones necesarias para desarrollo._

## Estructura de Carpetas para Codespaces

## Cómo usar docker-compose.override.yml en Codespaces
1. Abre el proyecto en Codespaces.
2. Asegúrate de que `docker-compose.override.yml` esté dentro de `.devcontainer/`.
3. Codespaces leerá automáticamente este archivo y lo combinará con `docker-compose.yml`.
4. Si necesitas levantar los servicios manualmente:
   ```bash
   docker-compose up -d
   ```
5. Verifica que los contenedores de Odoo, PostgreSQL y Redis estén en ejecución:
   ```bash
   docker ps
   ```
6. Accede a Odoo en `http://localhost:8069` dentro de Codespaces (o el puerto asignado).



## Ejemplo de docker-compose.override.yml para Codespaces
```yaml
version: '3.7'
services:
  odoo:
    build:
      context: .
    volumes:
      - ./custom_addons:/mnt/extra-addons
      - ./oca_addons:/mnt/oca-addons
      - ./github_addons:/mnt/github-addons
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
    ports:
      - "8069:8069"
  db:
    image: postgres:12
    environment:
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_DB=postgres
    ports:
      - "5432:5432"
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```
_Este archivo configura un entorno de desarrollo para Codespaces con Odoo, PostgreSQL y Redis._

```
/
├── custom_addons/                # Módulos personalizados de Odoo
│   ├── ofitec_core/
│   ├── ofitec_theme/
│   ├── ofitec_security/
│   ├── site_management/
│   ├── project_financials/
│   ├── project_risk/
│   ├── docuchat_ai/
│   └── ai_bridge/
├── oca_addons/                   # Módulos importados de OCA
├── github_addons/                # Conectores de GitHub (WhatsApp, Prometheus)
├── docs/                         # Documentación (incluye este archivo)
│   └── OFITEC_DEV_STRATEGY.md
├── scripts/                      # Scripts de automatización y herramientas de desarrollo
├── tests/                        # Pruebas unitarias e integración
├── .devcontainer/                # Configuración de Codespaces
│   ├── devcontainer.json
│   └── docker-compose.override.yml
├── docker-compose.yml            # Contenedor principal de Odoo, PostgreSQL, Redis
├── requirements.txt              # Dependencias de Python
├── README.md
└── .gitignore
```
_Esta estructura garantiza orden, escalabilidad y compatibilidad con Codespaces._


## Diagramas de Flujos de Uso

## Flujos de Datos de Integración de WhatsApp y Gestión de Obra
### Descripción Paso a Paso
1. El supervisor envía un mensaje por WhatsApp con el avance diario.
2. `whatsapp_connector` recibe el mensaje y lo transforma en datos estructurados.
3. Los datos son registrados automáticamente en `site_management`.
4. `site_management` actualiza el progreso y lo envía a `ai_bridge` para análisis predictivo.
5. `ai_bridge` evalúa el impacto en riesgos y genera alertas si corresponde.
6. El Project Manager recibe las alertas y valida el avance desde su dashboard.

## Diagrama de Flujo de Integración de WhatsApp y Gestión de Obra
```python
from graphviz import Digraph

whatsapp_flow = Digraph('OfitecWhatsAppFlow', format='png')

# Roles y módulos
whatsapp_flow.node('Supervisor', 'Supervisor', shape='box')
whatsapp_flow.node('whatsapp_connector', 'whatsapp_connector')
whatsapp_flow.node('site_management', 'site_management')
whatsapp_flow.node('ai_bridge', 'ai_bridge')
whatsapp_flow.node('project_manager', 'Project Manager', shape='box')

# Flujos
whatsapp_flow.edge('Supervisor', 'whatsapp_connector', label='Envía mensaje de avance')
whatsapp_flow.edge('whatsapp_connector', 'site_management', label='Registra progreso automáticamente')
whatsapp_flow.edge('site_management', 'ai_bridge', label='IA analiza progreso')
whatsapp_flow.edge('ai_bridge', 'project_manager', label='Genera alerta de avance')

print(whatsapp_flow.source)
```
_Este script genera un diagrama mostrando la integración de WhatsApp con la gestión de obra y la IA en OFITEC._

## Flujos de Datos de Aprobación de Documentos e IA
### Descripción Paso a Paso
1. El Project Manager sube un documento al módulo `documents`.
2. `documents` envía automáticamente el archivo a `docuchat_ai` para indexación.
3. `docuchat_ai` analiza el contenido y lo hace accesible para búsquedas inteligentes.
4. El Project Manager revisa los documentos indexados y aprueba los relevantes.
5. `ai_bridge` procesa datos de proyectos y evalúa riesgos relacionados.
6. `project_risk` recibe los resultados de la IA y genera alertas para el Gerente.

## Diagrama de Flujo de Aprobación de Documentos e IA
```python
from graphviz import Digraph

approval_ai_flow = Digraph('OfitecApprovalAndAIFlow', format='png')

# Roles y módulos
approval_ai_flow.node('ProjectManager', 'Project Manager', shape='box')
approval_ai_flow.node('documents', 'documents')
approval_ai_flow.node('docuchat_ai', 'docuchat_ai')
approval_ai_flow.node('ai_bridge', 'ai_bridge')
approval_ai_flow.node('project_risk', 'project_risk')
approval_ai_flow.node('Gerente', 'Gerente', shape='box')

# Flujos de aprobación
approval_ai_flow.edge('ProjectManager', 'documents', label='Sube documentos')
approval_ai_flow.edge('documents', 'docuchat_ai', label='Indexa documentos')
approval_ai_flow.edge('docuchat_ai', 'ProjectManager', label='Consulta información')

# Flujos de IA
approval_ai_flow.edge('ai_bridge', 'project_risk', label='Predice riesgos')
approval_ai_flow.edge('project_risk', 'Gerente', label='Envía alertas')

print(approval_ai_flow.source)
```
_Este script genera un diagrama para mostrar cómo interactúan los roles con el flujo de aprobación de documentos y el análisis de IA en OFITEC._

## Flujos de Datos de Casos de Uso
### Descripción Paso a Paso
1. El Supervisor registra avances en `site_management`, lo que alimenta datos para `ai_bridge`.
2. `ai_bridge` analiza riesgos potenciales y actualiza `project_risk`.
3. El Project Manager consulta `project_financials` para evaluar costos asociados.
4. El Auditor utiliza `docuchat_ai` para buscar documentación relevante.
5. El Gerente visualiza en `ofitec_theme` los datos consolidados en dashboards.

## Diagramas de Flujos de Casos de Uso
```python
from graphviz import Digraph

use_cases = Digraph('OfitecUseCases', format='png')

# Roles y módulos
use_cases.node('Supervisor', 'Supervisor', shape='box')
use_cases.node('site_management', 'site_management')
use_cases.node('ai_bridge', 'ai_bridge')
use_cases.node('project_risk', 'project_risk')
use_cases.node('ProjectManager', 'Project Manager', shape='box')
use_cases.node('project_financials', 'project_financials')
use_cases.node('account', 'account')
use_cases.node('Auditor', 'Auditor', shape='box')
use_cases.node('docuchat_ai', 'docuchat_ai')

# Flujos de casos de uso
use_cases.edge('Supervisor', 'site_management', label='Registra avance')
use_cases.edge('site_management', 'ai_bridge', label='IA analiza avance')
use_cases.edge('ai_bridge', 'project_risk', label='Genera riesgos')
use_cases.edge('ProjectManager', 'project_financials', label='Revisa costos')
use_cases.edge('project_financials', 'account', label='Envía datos contables')
use_cases.edge('Auditor', 'docuchat_ai', label='Consulta documentos')

print(use_cases.source)
```
_Este script genera un diagrama de casos de uso mostrando cómo interactúan los roles con los módulos clave de OFITEC._

```python
from graphviz import Digraph

flow = Digraph('OfitecUsageFlows', format='png')

# Definir roles
roles = ['Supervisor', 'Project Manager', 'Gerente', 'Auditor']

# Definir módulos
modules = [
    'site_management', 'project_financials', 'project_risk', 'docuchat_ai', 'ai_bridge', 'account', 'ofitec_theme'
]

# Agregar nodos de roles
for r in roles:
    flow.node(r, r, shape='box')

# Agregar nodos de módulos
for m in modules:
    flow.node(m, m)

# Definir flujos
flow.edge('Supervisor', 'site_management', label='Registra avance')
flow.edge('site_management', 'ai_bridge', label='Analiza datos')
flow.edge('ai_bridge', 'project_risk', label='Genera riesgos')
flow.edge('Project Manager', 'project_financials', label='Revisa costos')
flow.edge('project_financials', 'account', label='Integra contabilidad')
flow.edge('Auditor', 'docuchat_ai', label='Consulta documentos')
flow.edge('Gerente', 'ofitec_theme', label='Visualiza dashboard')

print(flow.source)
```
_Este script genera un diagrama de los flujos de uso entre roles y módulos de OFITEC._


## Casos de Uso Prácticos por Módulo
### ofitec_core
- **Caso:** Centralizar datos de proyectos y usuarios para que todos los módulos accedan a una misma fuente de información.

### ofitec_theme
- **Caso:** Presentar un dashboard ejecutivo que combine métricas de obra, riesgos y finanzas en una sola vista.

### ofitec_security
- **Caso:** Un gerente solo puede ver información de proyectos asignados gracias a permisos dinámicos.

### site_management
- **Caso:** Un supervisor registra diariamente 200 m² de pavimento ejecutado, generando datos automáticos para costos y cronograma.

### project_financials
- **Caso:** Un gerente de finanzas revisa desviaciones de presupuesto y aprueba órdenes de cambio.

### project_risk
- **Caso:** Se detecta un retraso en obra y el sistema genera automáticamente un riesgo con recomendación de mitigación.

### docuchat_ai
- **Caso:** Un auditor busca "actas de recepción" y encuentra rápidamente documentos indexados en segundos.

### ai_bridge
- **Caso:** El sistema predice que el proyecto tendrá un sobrecosto del 8% si no se agregan recursos adicionales.

### project (Odoo)
- **Caso:** Un jefe de proyectos define hitos y tareas para controlar la ejecución de la obra.

### account (Odoo)
- **Caso:** El área contable emite facturas de avance basadas en datos reales de obra.

### hr (Odoo)
- **Caso:** Recursos humanos actualiza permisos y roles para nuevos empleados de obra.

### queue_job (OCA)
- **Caso:** Un proceso pesado de indexación de documentos se ejecuta en segundo plano sin afectar la operación.

### odoo-whatsapp-connector (GitHub)
- **Caso:** Un supervisor informa desde WhatsApp que terminó un tramo de obra y el avance se actualiza automáticamente.

### odoo-prometheus-exporter (GitHub)
- **Caso:** El equipo de TI monitorea métricas de Odoo en Grafana para detectar cuellos de botella de rendimiento.


### Descripción Detallada de Módulos

#### ofitec_core
- **Objetivo:** Servir como núcleo del sistema, gestionando modelos base y la API central.
- **Qué hace:** Define entidades principales (proyectos, usuarios extendidos, configuraciones globales).
- **Qué muestra:** Datos unificados de referencia para otros módulos.
- **Importa:** Usuarios de Odoo, proyectos de `project`.
- **Exporta:** Datos consolidados para módulos como `site_management`, `project_financials`.
- **Analiza/Explica:** No analiza, solo normaliza y estructura datos.
- **Importancia:** Sin este módulo no existiría un punto central de datos.

#### ofitec_theme
- **Objetivo:** Proveer interfaz visual adaptada al branding de OFITEC.
- **Qué hace:** Personaliza vistas, dashboards y componentes OWL.
- **Qué muestra:** Paneles ejecutivos, métricas y KPIs.
- **Importa:** Datos desde todos los módulos operativos.
- **Exporta:** Visualización amigable.
- **Analiza/Explica:** Presenta métricas y datos relevantes de forma comprensible.
- **Importancia:** Es clave para la usabilidad y adopción por parte de los usuarios.

#### ofitec_security
- **Objetivo:** Controlar permisos y roles avanzados.
- **Qué hace:** Define reglas de acceso dinámicas por proyecto y grupo.
- **Qué muestra:** No tiene vistas frontales, solo afecta permisos.
- **Importa:** Roles de Odoo (`hr` y `res.users`).
- **Exporta:** Restricciones de seguridad.
- **Analiza/Explica:** Explica accesos denegados y permisos aplicados.
- **Importancia:** Garantiza integridad y confidencialidad de datos.

#### site_management
- **Objetivo:** Gestionar avances de obra y reportes diarios.
- **Qué hace:** Registra progreso, incidencias y asistencia.
- **Qué muestra:** Reportes de avance, indicadores de productividad.
- **Importa:** Datos de proyectos y usuarios.
- **Exporta:** Información de progreso para finanzas y riesgos.
- **Analiza/Explica:** Genera informes de avance para gerencia.
- **Importancia:** Es el corazón operativo de las obras.

#### project_financials
- **Objetivo:** Integrar control financiero con datos de obra.
- **Qué hace:** Gestiona presupuestos, órdenes de cambio, flujos de caja.
- **Qué muestra:** Estado financiero por proyecto.
- **Importa:** Avances de `site_management`.
- **Exporta:** Información a contabilidad (`account`).
- **Analiza/Explica:** Proyecciones de costos y desviaciones.
- **Importancia:** Es clave para la rentabilidad y control de proyectos.

#### project_risk
- **Objetivo:** Identificar y gestionar riesgos de proyecto.
- **Qué hace:** Registra riesgos derivados de incidentes y predicciones IA.
- **Qué muestra:** Listados de riesgos con planes de mitigación.
- **Importa:** Datos de `site_management` y `ai_bridge`.
- **Exporta:** Alertas a gerencia.
- **Analiza/Explica:** Evalúa probabilidad e impacto de riesgos.
- **Importancia:** Reduce pérdidas y problemas futuros.

#### docuchat_ai
- **Objetivo:** Centralizar documentos y permitir búsqueda inteligente.
- **Qué hace:** Indexa archivos y permite consultas con IA.
- **Qué muestra:** Resultados de búsqueda contextualizados.
- **Importa:** Documentos de `documents` y Google Drive.
- **Exporta:** Datos indexados para consultas rápidas.
- **Analiza/Explica:** Analiza contenido documental para extraer datos clave.
- **Importancia:** Optimiza tiempos de consulta y evita pérdida de información.

#### ai_bridge
- **Objetivo:** Potenciar decisiones con análisis predictivo.
- **Qué hace:** Procesa datos de obra, finanzas y riesgos para generar predicciones.
- **Qué muestra:** Alertas y recomendaciones.
- **Importa:** Datos de `site_management`, `project_risk`, `project_financials`.
- **Exporta:** Sugerencias y análisis predictivo.
- **Analiza/Explica:** Identifica patrones y tendencias para anticipar problemas.
- **Importancia:** Permite decisiones proactivas en la gestión de proyectos.

## Integración de Métricas de Cobertura en Grafana
- Exportar métricas de cobertura de `pytest-cov` a Prometheus utilizando un exportador intermedio.
- Crear un dashboard en Grafana con:
  - % de cobertura por módulo (`ofitec_core`, `site_management`, `ai_bridge`, etc.).
  - Tendencia histórica de cobertura.
  - Alertas si la cobertura cae por debajo de un umbral (por ejemplo, 80%).

### Ejemplo de Exportación de Cobertura
```yaml
scrape_configs:
  - job_name: 'coverage'
    static_configs:
      - targets: ['coverage-exporter:9090']
```

### Ejemplo de Panel Grafana
- Panel 1: Gráfico de líneas de cobertura por módulo.
- Panel 2: Tabla comparativa de cobertura vs. umbral definido.
- Panel 3: Alertas de descenso de cobertura integradas con Slack o correo electrónico.

## Reporte de Cobertura de Código y Métricas de Calidad en CI/CD
### Ejemplo de configuración extendida de GitHub Actions
```yaml
name: Run Tests with Coverage

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8
      - name: Run tests with coverage
        run: |
          pytest --cov=custom_addons --cov-report=xml
      - name: Lint code
        run: |
          flake8 custom_addons --max-line-length=100
      - name: Upload coverage report
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```
_Este pipeline ejecuta pruebas, genera reporte de cobertura y valida la calidad de código._


## Automatización de Pruebas en CI/CD con GitHub Actions
### Ejemplo de workflow
```yaml
name: Run Pytest

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:12
        ports:
          - 5432:5432
        env:
          POSTGRES_PASSWORD: odoo
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --maxfail=1 --disable-warnings -q
```
_Este pipeline ejecuta automáticamente las pruebas Pytest para todos los módulos de OFITEC al hacer push o crear un pull request._


## Pruebas de Integración de Flujos Completos
### Ejemplo: Flujo Completo de Proyecto
```python
import pytest

def test_full_project_flow(env):
    # Crear proyecto
    project = env['project.project'].create({'name': 'Proyecto Integral'})

    # Registrar avance en site_management
    env['ofitec.daily.report'].create({'project_id': project.id, 'progress': 20})

    # Actualizar costos en project_financials
    financial = env['ofitec.project.financials'].create({'project_id': project.id, 'cost_rate': 1000})
    financial.update_costs_from_progress(project.id)
    assert financial.progress_cost > 0

    # Registrar riesgo desde incidentes
    risk = env['ofitec.project.risk'].create({'project_id': project.id, 'description': 'Retraso'})
    assert risk

    # Indexar documentos en docuchat_ai
    env['docuchat.ai'].create({'name': 'Plano.pdf', 'project_id': project.id})

    # Ejecutar análisis IA
    result = env['ai.bridge'].analyze_risk(project)
    assert isinstance(result, dict)

    # Validar integración contable
    invoice = env['account.move'].create_invoice_from_budget(financial)
    assert invoice
```

## Pruebas Automatizadas para IA y Análisis de Sentimiento
### Ejemplo: IA Predicción de Costos
```python
import pytest

def test_ai_predict_costs(env):
    project = env['project.project'].create({'name': 'AI Test'})
    result = env['ai.bridge'].predict_costs(project)
    assert 'predicted_cost' in result
```

### Ejemplo: Análisis de Sentimiento WhatsApp
```python
import pytest

def test_sentiment_analysis(env):
    message = 'Estamos retrasados y hay problemas'
    sentiment = env['ai.sentiment'].analyze_message(message)
    assert sentiment in ['negative', 'neutral', 'positive']
```

## Pruebas Automatizadas para Notificaciones en Tiempo Real
### Ejemplo: Redis
```python
import pytest
import redis

def test_publish_redis_notification(monkeypatch):
    mock_redis = redis.Redis()
    monkeypatch.setattr(mock_redis, 'publish', lambda *a, **k: 1)
    result = mock_redis.publish('ofitec_notifications', 'Test message')
    assert result == 1
```

### Ejemplo: Odoo bus.bus
```python
import pytest

def test_send_bus_notification(env):
    bus = env['bus.bus']
    bus._sendone('project_updates', 'message', {'title': 'Test', 'body': 'Notification'})
    # Si no hay excepción, se considera exitoso
    assert True
```

## Pruebas Automatizadas para Cron Jobs y Colas
### Ejemplo: Cron Sync Google Drive
```python
import pytest

def test_cron_sync_drive(env):
    service = env['ofitec.drive.service'].create({})
    service.sync_drive_files()
    # Validar que no hay errores y que los archivos se sincronizaron correctamente
    assert True
```

### Ejemplo: Queue Job IA
```python
import pytest

def test_queue_ai_job(env):
    job = env['queue.job'].create({'name': 'AI Risk Analysis'})
    assert job.state in ['pending', 'started']
```

## Pruebas Automatizadas de Integración API
### Ejemplo: Google Drive
```python
import pytest

def test_upload_file(monkeypatch):
    from ofitec_drive.services import upload_file

    class MockDrive:
        def CreateFile(self, meta):
            class File:
                def SetContentFile(self, path): pass
                def Upload(self): return True
            return File()

    monkeypatch.setattr('ofitec_drive.services.GoogleDrive', lambda auth: MockDrive())
    result = upload_file('dummy.txt', 'folder123')
    assert result is True
```

### Ejemplo: WhatsApp API
```python
import pytest
import requests

def test_send_whatsapp_message(monkeypatch):
    from ofitec_whatsapp.services import send_whatsapp_message

    class MockResponse:
        def json(self): return {"status": "sent"}

    monkeypatch.setattr(requests, 'post', lambda *a, **k: MockResponse())
    response = send_whatsapp_message('+56912345678', 'Hola')
    assert response['status'] == 'sent'
```

## Pruebas Automatizadas con Pytest
### Ejemplo: site_management → project_financials
```python
import pytest

@pytest.mark.parametrize('progress,cost_rate,expected', [
    (50, 1000, 50000),
    (30, 800, 24000)
])
def test_update_costs_from_progress(env, progress, cost_rate, expected):
    project = env['ofitec.project.financials'].create({'name': 'Test', 'cost_rate': cost_rate})
    env['ofitec.daily.report'].create({'project_id': project.id, 'progress': progress})
    project.update_costs_from_progress(project.id)
    assert project.progress_cost == expected
```

### Ejemplo: ai_bridge → project_risk
```python
import pytest

def test_analyze_risk(env):
    project = env['project.project'].create({'name': 'Risk Test'})
    env['ofitec.project.risk'].create({'project_id': project.id, 'description': 'Prueba', 'severity': 'medium'})
    result = env['ai.bridge'].analyze_risk(project)
    assert isinstance(result, dict)  # Ejemplo validando estructura de respuesta
```



### Relación de Módulos con Flujos de Trabajo
- **project (Odoo):** Base para planificación y cronogramas → soporte de flujos de obra.
- **account (Odoo):** Base financiera → integrado en flujos de `project_financials`.
- **hr (Odoo):** Control de usuarios y permisos → alimenta `ofitec_security`.
- **queue_job (OCA):** Procesos en segundo plano → sincronización Drive y tareas IA.
- **ofitec_core (Propio):** API de datos → usado por todos los módulos.
- **ofitec_security (Propio):** Control de permisos → interfiere en todos los flujos.
- **site_management (Propio):** Reportes diarios → conecta con `ai_bridge` para análisis.
- **project_financials (Propio):** Presupuestos y costos → se nutre de `site_management`.
- **project_risk (Propio):** Evaluación de riesgos → recibe datos de obra e IA.
- **docuchat_ai (Propio):** Indexación documental → vinculado a `documents` y Drive.
- **ai_bridge (Propio):** Motor IA → soporta flujos de obra, riesgos y finanzas.
- **odoo-whatsapp-connector (GitHub):** Integración de WhatsApp → para avances y notificaciones.

Estas relaciones aseguran que cada módulo esté claramente alineado con los flujos de negocio y evitan redundancias, optimizando el ecosistema OFITEC.

### Módulos Odoo Originales

#### project
- **Objetivo:** Base de planificación y control de proyectos.
- **Qué hace:** Gestiona tareas y cronogramas.
- **Importa:** Datos de usuarios y recursos.
- **Exporta:** Información de proyectos usada por `site_management`.
- **Importancia:** Punto de partida de la estructura de gestión.

#### account
- **Objetivo:** Contabilidad central.
- **Qué hace:** Procesa facturas y registros contables.
- **Importa:** Datos de presupuestos y costos.
- **Exporta:** Estados financieros consolidados.
- **Importancia:** Conecta operaciones de obra con el área financiera.

#### hr
- **Objetivo:** Gestión de empleados y permisos.
- **Qué hace:** Administra usuarios y roles.
- **Importa:** Información de personal.
- **Exporta:** Permisos a `ofitec_security`.
- **Importancia:** Define seguridad y control de accesos.

#### purchase
- **Objetivo:** Control de compras.
- **Qué hace:** Registra solicitudes y órdenes de compra.
- **Importa:** Datos de inventario y proveedores.
- **Exporta:** Costos a contabilidad.
- **Importancia:** Control de abastecimiento para proyectos.

#### stock
- **Objetivo:** Gestionar inventarios.
- **Qué hace:** Administra entradas y salidas de materiales.
- **Importa:** Órdenes de compra.
- **Exporta:** Datos de consumo a finanzas.
- **Importancia:** Relaciona recursos con costos de obra.

#### mail
- **Objetivo:** Comunicación interna.
- **Qué hace:** Maneja mensajes y seguimiento de tareas.
- **Importa:** Datos de usuarios y tareas.
- **Exporta:** Notificaciones y registros.
- **Importancia:** Canal transversal de comunicación.

#### documents
- **Objetivo:** Gestión documental.
- **Qué hace:** Almacena y organiza archivos.
- **Importa:** Archivos de usuarios y Drive.
- **Exporta:** Base documental a `docuchat_ai`.
- **Importancia:** Fuente principal de información documental.

#### bus
- **Objetivo:** Envío de notificaciones en tiempo real.
- **Qué hace:** Dispara mensajes internos.
- **Importa:** Eventos de módulos.
- **Exporta:** Alertas en tiempo real a usuarios.
- **Importancia:** Garantiza reactividad del sistema.
- **project:** Base para gestión de tareas y cronogramas.
- **account:** Contabilidad e integración financiera.
- **hr:** Gestión de personal y permisos.
- **purchase:** Gestión de adquisiciones y órdenes de compra.
- **stock:** Control de inventario de materiales de obra.
- **mail:** Comunicación interna y registro de actividades.
- **documents:** Gestión documental básica.
- **bus:** Soporte de notificaciones en tiempo real.
**Justificación:** Estos módulos son estándar y proveen funcionalidades básicas que serán extendidas por los módulos propios de OFITEC.

### Módulos OCA

#### queue_job
- **Objetivo:** Procesar tareas pesadas en segundo plano.
- **Qué hace:** Ejecuta jobs asincrónicos como sincronización con Google Drive o análisis IA.
- **Importa:** Datos de módulos que envían tareas.
- **Exporta:** Resultados de ejecución.
- **Importancia:** Mejora rendimiento y evita bloqueos del servidor.

#### project_task_dependency
- **Objetivo:** Gestionar dependencias entre tareas.
- **Qué hace:** Define predecesores y sucesores en tareas de proyecto.
- **Importa:** Datos de `project`.
- **Exporta:** Relaciones de tareas para mejor planificación.
- **Importancia:** Permite una gestión de proyectos más realista.

#### contract
- **Objetivo:** Administración avanzada de contratos.
- **Qué hace:** Gestiona vigencias, renovaciones y términos contractuales.
- **Importa:** Datos de clientes y proyectos.
- **Exporta:** Información a finanzas.
- **Importancia:** Vincula contratos a ejecución y pagos.

#### account_financial_tools
- **Objetivo:** Complementar funcionalidades financieras.
- **Qué hace:** Agrega reportes y herramientas contables adicionales.
- **Importa:** Datos de `account`.
- **Exporta:** Informes financieros avanzados.
- **Importancia:** Soporte para análisis contable detallado.

#### server-tools
- **Objetivo:** Aportar utilidades técnicas para administración.
- **Qué hace:** Proporciona herramientas de servidor para mejorar estabilidad.
- **Importa:** Configuraciones de sistema.
- **Exporta:** Funciones reutilizables.
- **Importancia:** Base técnica para personalizaciones.

#### google_drive_connector
- **Objetivo:** Conectar Odoo con Google Drive.
- **Qué hace:** Permite sincronizar documentos entre Odoo y Drive.
- **Importa:** Archivos de Google Drive.
- **Exporta:** Documentos organizados en Odoo.
- **Importancia:** Simplifica el acceso a documentación externa.

### Módulos GitHub

#### odoo-whatsapp-connector
- **Objetivo:** Integración directa con WhatsApp Business API.
- **Qué hace:** Envía y recibe mensajes desde Odoo.
- **Importa:** Datos de contactos y proyectos.
- **Exporta:** Historial de mensajes vinculados a proyectos.
- **Importancia:** Comunicación directa con personal en obra.

#### odoo-prometheus-exporter
- **Objetivo:** Exponer métricas de Odoo a Prometheus.
- **Qué hace:** Publica KPIs de sistema y rendimiento.
- **Importa:** Datos de logs y rendimiento de Odoo.
- **Exporta:** Métricas en formato Prometheus.
- **Importancia:** Base para monitoreo en Grafana.
- **queue_job:** Procesamiento asíncrono para tareas pesadas.
- **project_task_dependency:** Manejo de dependencias entre tareas de proyecto.
- **contract:** Administración avanzada de contratos.
- **account_financial_tools:** Herramientas contables extendidas.
- **server-tools:** Utilidades generales para administración del sistema.
- **google_drive_connector (si aplica):** Conector inicial con Google Drive.
**Justificación:** Estos módulos reducen el tiempo de desarrollo y están respaldados por la comunidad, garantizando estabilidad.

### Módulos GitHub
- **odoo-whatsapp-connector:** Integración inicial con WhatsApp.
- **odoo-prometheus-exporter:** Métricas de Odoo para Prometheus.
**Justificación:** Soluciones open source que permiten implementar integraciones críticas sin desarrollarlas desde cero.

### Módulos de Desarrollo Propio

## Ejemplos Técnicos de Flujos de Datos
### site_management → project_financials
```python
class ProjectFinancials(models.Model):
    _inherit = 'ofitec.project.financials'

    def update_costs_from_progress(self, project_id):
        progress = self.env['ofitec.daily.report'].search([('project_id','=',project_id)])
        total_progress = sum(progress.mapped('progress'))
        self.write({'progress_cost': total_progress * self.cost_rate})
```

### site_management → project_risk
```python
class ProjectRisk(models.Model):
    _inherit = 'ofitec.project.risk'

    def create_risk_from_incident(self, incident):
        self.create({
            'name': incident.name,
            'severity': 'medium',
            'project_id': incident.project_id.id
        })
```

### project_financials → account
```python
class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_invoice_from_budget(self, budget):
        self.create({
            'move_type': 'out_invoice',
            'partner_id': budget.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': budget.name,
                'quantity': 1,
                'price_unit': budget.amount
            })]
        })
```

### docuchat_ai → documents
```python
class DocuChatIndexer:
    def index_document(self, document):
        text = self.extract_text(document)
        self.store_embeddings(text)
```

### ai_bridge → site_management y project_risk
```python
class AIBridge:
    def analyze_risk(self, project):
        risks = self.env['ofitec.project.risk'].search([('project_id','=',project.id)])
        return self.model.predict(risks)
```

## Flujos de Datos entre Módulos
### Descripción Paso a Paso
1. `site_management` genera reportes de avance que se integran en `project_financials` para actualizar costos.
2. Las incidencias en `site_management` se registran como riesgos en `project_risk`.
3. `project_financials` envía información contable a `account` para consolidación financiera.
4. `docuchat_ai` indexa documentos cargados en `documents` para consultas inteligentes.
5. `ai_bridge` analiza datos de `site_management` y `project_risk` para generar predicciones.
6. `queue_job` ejecuta tareas pesadas en segundo plano, como sincronización de Drive e indexación IA.

## Diagrama de Dependencias de Datos
```python
from graphviz import Digraph

diagram = Digraph('OfitecDataDependencies', format='png')

modules = [
    'site_management', 'project_financials', 'project_risk', 'docuchat_ai', 'ai_bridge', 'queue_job', 'account', 'documents'
]

for m in modules:
    diagram.node(m, m)

diagram.edge('site_management', 'project_financials')
diagram.edge('site_management', 'project_risk')
diagram.edge('project_financials', 'account')
diagram.edge('docuchat_ai', 'documents')
diagram.edge('ai_bridge', 'site_management')
diagram.edge('ai_bridge', 'project_risk')
diagram.edge('queue_job', 'ai_bridge')
diagram.edge('queue_job', 'docuchat_ai')

print(diagram.source)
```
_Este script genera el diagrama de dependencias de datos entre los módulos de OFITEC._
![Diagrama de Dependencias de Datos](attachment://ofitec_data_dependencies_diagram.png)
_Este diagrama muestra cómo fluyen los datos entre módulos como site_management, project_financials, project_risk, docuchat_ai, ai_bridge y queue_job._



### Dependencias de Datos entre Módulos
- `site_management` ↔ `project_financials`: Los avances de obra generan impacto en costos y presupuestos.
- `site_management` ↔ `project_risk`: Las incidencias detectadas se transforman en riesgos evaluados.
- `project_financials` ↔ `account`: Los movimientos financieros se registran en contabilidad.
- `docuchat_ai` ↔ `documents`: Los documentos cargados en Odoo son indexados automáticamente para búsqueda inteligente.
- `ai_bridge` ↔ `site_management` y `project_risk`: La IA consume datos de obra y riesgos para generar predicciones.
- `queue_job` ↔ Todos los módulos que ejecutan tareas pesadas (Drive sync, IA, indexación).


- **ofitec_core:** API central y modelos de datos.
- **ofitec_theme:** Interfaz visual adaptada al estilo OFITEC.
- **ofitec_security:** Roles, permisos avanzados y control por proyectos.
- **site_management:** Reportes diarios, avances de obra y control en terreno.
- **project_financials:** Gestión financiera de proyectos.
- **project_risk:** Identificación y seguimiento de riesgos con IA.
- **docuchat_ai:** Indexación de documentos y búsqueda con IA.
- **ai_bridge:** Motor de análisis y predicciones para obra, finanzas y riesgos.
**Justificación:** Son el núcleo diferencial de OFITEC, diseñados específicamente para el sector de construcción y urbanización.

