# Hoja de Ruta del Proyecto OFITEC.AI - Basado en Odoo

## Base del Proyecto (Estrategia Técnica)

### Arquitectura General
- Backend: Odoo 16 (Python 3.8+, PostgreSQL 12+)
- Frontend: OWL, SCSS modular
- Infraestructura: Docker Compose, CI/CD con GitHub Actions
- Servicios externos: Google Drive API, WhatsApp Cloud API, IA (LangChain + Transformers)
- Mensajería: Redis/RabbitMQ

### Módulos y Relaciones
- ofitec_core: API central y base de datos
- ofitec_theme: UI conectada a ofitec_core
- ofitec_security: Roles, permisos y control de acceso
- site_management: Relacionado con project_documents y ai_bridge
- project_financials: Vinculado a site_management y account
- project_risk: Integrado con IA
- docuchat_ai: Conecta documentos y Drive
- ai_bridge: Motor de predicciones

#### Dependencias
- site_management depende de ofitec_core y ofitec_security
- project_financials depende de site_management y account
- project_risk depende de ai_bridge y site_management
- docuchat_ai depende de documents y Drive

### Roles y Permisos
- Administrador: Acceso total
- Gerente General: Dashboards, riesgos, finanzas
- Project Manager: Control de obra, documentos
- Supervisor: Reportes diarios, inspecciones
- Estudio de Propuestas: Consulta documentos y presupuestos
- Permisos avanzados por proyecto

### Flujos Principales
1. Avances → IA valida → Dashboard
2. Documentos → Drive Sync → DocuChat indexa
3. Presupuestos → Financials → IA proyecta
4. Riesgos → AI Bridge analiza → Alertas
5. WhatsApp → Registro y análisis de sentimiento

### Integración de IA con Workflows
- Validación automática de avances
- Recomendaciones de reasignación
- Alertas de desviaciones por WhatsApp

### Análisis de Sentimiento
- Procesamiento con Transformers
- Métricas de estado de equipo
- Alertas automáticas por patrones negativos

### Flujo de Aprobación de Documentos
- mail.activity para flujos de aprobación
- Reglas por rol (PM planos, Gerencia presupuestos)

### Monitoreo y Logs
- Prometheus para métricas
- Grafana para dashboards
- ELK Stack para auditoría

## Visión General
Este proyecto se basa en Odoo 16 y busca implementar innovaciones avanzadas en gestión de proyectos de construcción, integrando IA, UX mejorada, optimización y análisis de datos. La hoja de ruta se deriva de las entregas de innovación proporcionadas, organizadas en fases secuenciales.

## Arquitectura Base
- **Backend**: Odoo 16 (Python 3.8+, PostgreSQL 12+)
- **Frontend**: OWL, SCSS modular
- **Infraestructura**: Docker Compose, CI/CD con GitHub Actions
- **Integraciones**: Google Drive API, WhatsApp Cloud API, IA (LangChain + Transformers)
- **Mensajería**: Redis/RabbitMQ

## Fases del Proyecto

### Fase 1: Propuestas de Innovación y Implementación Inicial (Agosto 9, 2025)
**Entregas: 0, 1, 2**

#### Entrega 0: Propuesta de Innovación Total
- Experiencia de Usuario (UX): Command Palette, Home Next-Best-Action, Comparador de escenarios, Timeline 360°, Redacción asistida, Aprendizaje in-product, Modo Móvil Offline-first.
- IA útil: Copilotos por rol (PM, Finanzas/CEO, Terreno, Compras), Trust & Audit.
- Optimización: Planificador con OR-Tools, Digital Twin de Obra, Cashflow Lab.
- Datos: WBS canónica, Data Contracts, RAG de documentos.
- Compras: Smart RFQ, Trust Graph, Lead-time tracking.
- QHSE: Form builder, Visión por computadora.

#### Entrega 1: Código Listo para Pegar
- Command Palette (⌘K)
- Next-Best-Action
- Comparador de Escenarios
- Cashflow Lab
- Form Builder QHSE
- API GraphQL + Webhooks
- PWA Offline
- Smart RFQ v1

#### Entrega 2: Comparador OWL, Offline Sync, GraphQL, Optimizador
- Comparador OWL lado a lado para Escenarios
- Sincronización Offline con cola (PWA)
- API GraphQL completa
- Optimizador de Planificación (heurístico + OR-Tools)

**Milestone**: Implementación de UX core y sincronización offline.

### Fase 2: Características Avanzadas de UX e IA (Agosto 10, 2025)
**Entregas: 3, 4, 5**

#### Entrega 3: QHSE Vision GraphQL Offline con Adjuntos CEO Dashboard
- Integración QHSE con GraphQL
- Soporte offline para adjuntos
- Dashboard para CEO

#### Entrega 4: Anotación Visual GraphQL Series CEO Subida con Progreso
- Anotaciones visuales
- Series de datos para CEO
- Indicadores de progreso

#### Entrega 5: Optimizador Avanzado CEO KPIs Pro QA Automatizada
- Optimizador avanzado
- KPIs para CEO
- QA automatizada

**Milestone**: Dashboards avanzados y optimización de procesos.

### Fase 3: Capacidad, Pruebas y Despliegue (Agosto 10, 2025)
**Entregas: 6, 7**

#### Entrega 6: Capacidad Acumulativa Overtime Aging AR/AP Lead Time Tests HTTP
- Gestión de capacidad acumulativa
- Overtime y aging
- Pruebas HTTP para lead times

#### Entrega 6: Capacidad Acumulativa Overtime AR/AP Aging Tests E2E
- Pruebas end-to-end
- Integración con AR/AP

#### Entrega 7: Despliegue Hardening Docker Backups Monitoreo Google SSO SII F29
- Hardening de despliegue
- Docker y backups
- Monitoreo
- Integración Google SSO
- SII F29

**Milestone**: Infraestructura robusta y pruebas completas.

### Fase 4: CI/CD, Escalabilidad y Exportación (Agosto 10, 2025)
**Entregas: 8, 9**

#### Entrega 8: CI/CD Backup Remoto Cifrado Alertas Slack Email F29 Mapeo Exportación
- CI/CD pipeline
- Backups remotos cifrados
- Alertas (Slack, Email)
- Mapeo y exportación F29

#### Entrega 9: Autoscaling Workers Blue Green Exportación SII Avanzada Runbooks DR
- Autoscaling de workers
- Despliegue blue-green
- Exportación SII avanzada
- Runbooks para DR

**Milestone**: Automatización de despliegue y recuperación de desastres.

### Fase 5: Alta Disponibilidad y Recuperación (Agosto 10, 2025)
**Entregas: 10, 11, 12**

#### Entrega 10: Blue Green Automático WAL Standby CSP F29 Completo
- Despliegue blue-green automático
- WAL standby
- CSP completo
- F29

#### Entrega 11: Failover Automático CSP Report Only Enforce Vault de Secretos SII Exploratorio
- Failover automático
- Report only mode
- Vault de secretos
- Exploración SII

#### Entrega 12: Failover Multi Region Rotación Automática de Secretos ETL Financiero Avanzado
- Failover multi-region
- Rotación automática de secretos
- ETL financiero avanzado

**Milestone**: Alta disponibilidad y seguridad avanzada.

### Fase 6: Análisis de Datos y Visualización (Agosto 10, 2025)
**Entregas: 13, 14**

#### Entrega 13: Activo Activo Lecturas Catálogo Linaje de Datos Dashboards Pack
- Configuración activo-activo
- Lecturas de catálogo
- Linaje de datos
- Paquete de dashboards

#### Entrega 13: Activo Activo Lecturas Catálogo Linaje de Datos Dashboards Pack (1)
- Versión alternativa o complemento

#### Entrega 14: Postgres Analytics DuckDB Server SLOs de BI y Data Contracts
- Analytics con Postgres
- DuckDB server
- SLOs para BI
- Data contracts

**Milestone**: Plataforma de análisis completa.

## Cronograma General
- **Agosto 9, 2025**: Fase 1 (Propuestas e implementación inicial)
- **Agosto 10, 2025**: Fases 2-6 (Características avanzadas, pruebas, despliegue, HA, análisis)
- **Post-implementación**: Monitoreo, optimización y mantenimiento continuo.

## Dependencias y Riesgos
- Dependencias: Asegurar compatibilidad con Odoo 16 y módulos existentes.
- Riesgos: Integración con APIs externas, rendimiento de IA, cumplimiento normativo (SII, F29).
- Mitigación: Pruebas exhaustivas, documentación detallada, equipos de respaldo.

## Próximos Pasos
1. Revisar y validar cada entrega de código.
2. Configurar entorno de desarrollo con Docker.
3. Implementar módulos por fases.
4. Ejecutar pruebas de integración.
5. Desplegar en entorno de staging.
6. Monitoreo y ajustes finales.

Esta hoja de ruta proporciona una estructura clara para el desarrollo del proyecto OFITEC.AI, alineada con las innovaciones propuestas.</content>
<parameter name="filePath">/workspaces/OFITEC.AI/ofitec_project_roadmap.md
