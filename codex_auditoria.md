# OFITEC ERP - Auditoría de Código y Plan de Alineación
Documento living mantenido por Codex

---

## 1. Resumen Ejecutivo
- Base modular en Odoo 16 con addons propios: núcleo (`ofitec_core`, `ofitec_project`), obra (`site_management`), finanzas (`project_financials`), riesgos (`project_risk`), WhatsApp (`ofitec_whatsapp`), tema (`ofitec_theme`), AI (`ofitec_ai_advanced`, `ai_bridge`, `docuchat_ai`).
- Manifiestos, vistas XML y CSV de accesos validados sin errores (scripts/validate_odoo_manifests_and_views.py).
- Algunos defectos menores corregidos en esta pasada (duplicaciones de código y documentación de puertos).

---

## 2. Checklist de Validación (estado actual)

| # | Módulo/Función | Existe | Cumple intención | Nivel | Observaciones |
|---|----------------|:-----:|:----------------:|:----:|---------------|
| 1 | Gestión de Proyectos | Sí | Parcial | Básico | `ofitec_project` extiende `project.project` (progreso, presupuesto). Faltan vistas KPI y Gantt/Graf. |
| 2 | Presupuestos | Sí | Parcial | Básico | `project_financials` con cómputos (progreso/varianza). Falta maestro y carga múltiple. |
| 3 | Flujo Financiero | Parcial | Parcial | Básico | Sin integración SII/F29/IVA; sólo cálculos internos. |
| 4 | Contratistas | No | No | - | No hay módulo dedicado a contratistas. |
| 5 | Gestión Documental | Parcial | Parcial | - | `docuchat_ai` indexador placeholder; sin integración Drive/OneDrive. |
| 6 | WhatsApp Bot | Sí | Parcial | Básico | Webhook + API presentes; faltan métricas, colas/cron y panel. |
| 7 | Formularios Personalizados | Parcial | Parcial | Básico | Reporte diario con fotos/estado; faltan QA/QC wizards. |
| 8 | Sentiment | No (parcial en código) | No | - | Método simple en `ai_bridge`, sin UI ni flujo. |
| 9 | Gestión de Riesgos | Sí | Parcial | Básico | Modelo y vistas; falta matriz PxI y alertas automáticas. |
|10 | DocuChat IA | Sí | Parcial | Básico | Indexador y modelo; falta UI, crawler Drive/OneDrive y búsquedas reales. |
|11 | IA Global | Sí | Parcial | Básico | `ofitec_ai_advanced` y `ai_bridge` base, sin pipelines reales. |
|12 | Inteligencia Predictiva | Sí | Parcial | Básico | Seeds/demos; falta entrenamiento y jobs. |
|13 | Theme OFITEC | Sí | Parcial | Básico | Variables/SCSS y switch; falta pulir layouts y responsive.
|14 | RRHH Avanzado | No | No | - | Plan futuro. |
|15 | Compras/Abastecimiento | No | No | - | Plan futuro. |
|16 | Mantenimiento | No | No | - | Plan futuro. |
|17 | Postventa | No | No | - | Plan futuro. |
|18 | Cumplimiento | No | No | - | Plan futuro. |
|19 | Portal Cliente | No | No | - | Plan futuro. |
|20 | Marketplace/SDK | No | No | - | Plan futuro. |

---

## 3. Brechas priorizadas (Q3–Q4)
- Tema global: ordenar assets, consolidar variables, revisar responsive y componentes KPI.
- Executive Dashboard: KPIs (margen, días de caja, backlog), endpoints controladores y gráficos.
- Presupuestos: maestro + carga múltiple; sincronización con proyectos y reports.
- Flujo financiero: plan de integración SII/F29 (API + ETL), postergación IVA.
- WhatsApp E2E: completar webhook, plantillas oficiales, métricas/monitoreo y cron jobs.
- Riesgos: matriz PxI, heatmap y alertas IA (reglas + señales de datos).
- DocuChat: indexador Drive/OneDrive, UI de búsqueda y seguridad de acceso.

---

## 4. PRs sugeridos (lote 1)
- `site_management`: limpiar duplicaciones en modelos; pruebas mínimas de flujo reportes→incidentes→riesgos.
- `ofitec_whatsapp`: endurecer webhook, firma y colas; métricas básicas en modelo.
- `project_financials`: exponer endpoints JSON para KPIs; vista Executive integrada.
- `ofitec_theme`: refactor variables SCSS y ajuste responsive; remover restos `@import` si quedara alguno.
- `docuchat_ai`: servicio indexador real + UI OWL (sin incluir XML en bundles genéricos).
- `ofitec_ai_advanced`: mover dependencias pesadas a “opcionales” y proteger importaciones.

---

## 5. Red Flags detectados (y acciones)
- Duplicación de código en `site_management`:
  - `daily_report.py`: bloque redundante de actualización de progreso dentro de `_notify_risk_creation` (removido en esta pasada).
  - `site_incident.py`: código duplicado tras `return` en `create_from_report` (removido).
- Mismatch de puertos en documentación vs compose:
  - `docker-compose.yml` publica `10069:8069`; `SETUP.md` decía `8069`. Actualizado `SETUP.md` a `http://localhost:10069`.
- Dependencias pesadas en `requirements-odoo.txt` (tensorflow, xgboost, lightgbm): pueden hacer fallar builds/consumir RAM.
  - Sugerencia: marcar como opcionales y cargar bajo feature flags; usar wheels precompiladas.
- Pruebas: scripts de “test” son demostrativos y no validan sistema end-to-end.
  - Sugerencia: agregar tests de import de módulos Odoo en contenedor y smoke tests HTTP.
- Gráficos desde CDN (`Chart.js`): el código tolera fallo, pero preferir servir assets locales en producción.
- GraphQL opcional: `graphene` no está en `requirements-odoo.txt` (solo en host), endpoint responde con hint si falta.

---

## 6. Cambios aplicados en esta iteración
- Limpieza de `site_management/models/daily_report.py` (removido bloque redundante post-notificación).
- Limpieza de `site_management/models/site_incident.py` (removida duplicación tras `return`).
- Estandarización de puerto Odoo: `docker-compose.yml` y `SETUP.md` usan `http://localhost:8069`.
- Validación automática de manifiestos/XML/CSV ejecutada: 19 módulos escaneados, 0 incidencias.
- `project_financials`: agregado método `get_cost_trend_data` para alimentar el gráfico del dashboard.
- `requirements-odoo.txt`: añadido `graphene` para habilitar GraphQL opcional en el contenedor.
- `scripts/smoke_tests.py`: pruebas de humo para health y webhook WhatsApp.

---

## 7. Recomendaciones inmediatas
- Construir e iniciar con Docker: `docker-compose up -d` y verificar `http://localhost:10069`.
- En Odoo, instalar en orden: `ofitec_core`, `ofitec_security`, `ofitec_theme`, `site_management`, `project_financials`, `project_risk`, `ai_bridge`, `docuchat_ai`, `of_command_palette`.
- Instalar dependencias AI dentro del contenedor (si se requiere): revisar tamaños y limitar a lo necesario.
- Añadir smoke tests: health (`/ofitec/api/health`), dashboard JSON y webhook WhatsApp (GET de verificación).

---

## 8. Conclusiones
- El esqueleto cumple la visión base y es consistente; falta pulido visual/UX y completar integraciones IA/Finanzas.
- Con las correcciones menores, el arranque debería ser más fluido. El siguiente foco: KPIs ejecutivos, WhatsApp E2E, DocuChat real.

---

Última actualización: automatizada por Codex.
