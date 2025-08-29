# OFITEC ERP - Auditoría de Código y Plan de Alineación
Documento living mantenido por Codex

---

## 1. Visión del Proyecto
OFITEC no es un ERP tradicional.  
Debe convertirse en el **asistente digital inteligente de gestión de obras** para empresas constructoras, uniendo:

- **Núcleo sólido**: Proyectos, Presupuestos, Flujo Financiero, Contratistas.
- **Experiencia impecable**: UI/UX estilo fintech (tema DeFi verde, claro/oscuro).
- **IA aplicada**: sugerencias, predicciones y aprendizaje continuo de datos reales.
- **Integración total**: terreno ↔ oficina, WhatsApp ↔ Odoo ↔ SII ↔ Drive.
- **Innovación práctica**: anticipar problemas antes de que cuesten dinero.

---

## 2. Principios Rectores
Al validar el código, confirma que cumple con:
- **Modularidad**: cada módulo tiene responsabilidades claras, sin duplicar datos.
- **Un solo core de datos**: todo se alimenta desde las mismas tablas/base.
- **UX amigable**: simple, intuitivo, modo claro/oscuro.
- **IA embebida**: no como “extra”, sino integrada en flujo financiero, riesgos y planificación.
- **Interoperabilidad**: compatible con Odoo Community y OCA.

---

## 3. Módulos y Funcionalidades esperadas

### Núcleo
1. **Gestión de Proyectos**: Kanban, Gantt, Calendario, integración con Presupuestos/Contratistas.
2. **Presupuestos**: carga múltiple, presupuesto maestro, análisis IA desde Drive.
3. **Flujo Financiero**: reales vs planificados, integración SII/F29, postergación IVA.
4. **Contratistas**: ficha única, historial, desempeño, relación con proyectos.
5. **Gestión Documental (Drive Integration)**: integración con Google Drive/OneDrive, clasificación, permisos, catálogo en Odoo Community.

### Comunicación
6. **WhatsApp Bot**: avances diarios, asistencia, cuadrillas.
7. **Formularios Personalizados**: QA/QC, parte diario con fotos.
8. **Sentiment**: encuestas rápidas, IA analiza clima laboral.

### IA e Innovación
9. **Gestión de Riesgos**: matriz probabilidad/impacto + alertas IA.
10. **DocuChat IA (Drive-based)**: búsqueda en documentos con lenguaje natural, indexando contenido de Drive.
11. **IA Global**: sugerencias de planificación, compras, flujos financieros.
12. **Inteligencia Predictiva**: retrasos y sobrecostos anticipados.

### Estética
13. **Theme OFITEC**: modo claro/oscuro, estética DeFi verde, SCSS variables globales, switch en header.

### Extensiones (plan futuro)
14. Recursos Humanos Avanzado.
15. Compras y Abastecimiento Optimizado.
16. Mantenimiento de Equipos.
17. Postventa/Servicio Técnico.
18. Cumplimiento Normativo.
19. Portal Cliente Avanzado.
20. Marketplace/SDK.

---

## 4. Checklist de Validación (estado actual)

| # | Módulo/Función | ¿Existe? | ¿Cumple intención? | Nivel | Observaciones |
|---|---------------------|:------:|:------------------:|:-----:|-------------|
| 1 | Gestión de Proyectos | ✓ | ✓ | Básico | `ofitec_project` + Odoo Project. Faltan vistas custom y KPIs. |
| 2 | Presupuestos | ✓ | ~ | Básico | `project_financials` con cálculos. Falta maestro y carga múltiple. |
| 3 | Flujo Financiero | ~ | ~ | - | Sin implementación SII/F29/IVA. |
| 4 | Contratistas | ~ | ~ | - | No hay módulo específico. |
| 5 | Gestión Documental | ~ | ~ | - | Integración Drive pendiente. |
| 6 | WhatsApp Bot | ✓ | ~ | Básico | Config y envío; falta webhook/metrics. |
| 7 | Formularios Personalizados | ~ | ~ | - | Sin wizards QA/QC. |
| 8 | Sentiment | ~ | ~ | - | No implementado. |
| 9 | Gestión de Riesgos | ✓ | ~ | Básico | Modelo y vistas; falta matriz y alertas IA. |
|10 | DocuChat IA | ✓ | ~ | Básico | Placeholder; falta indexador real + UI. |
|11 | IA Global | ✓ | ~ | Básico | Base en `ofitec_ai_advanced`; falta integración. |
|12 | Inteligencia Predictiva | ✓ | ~ | Básico | Seed; falta entrenamiento real. |
|13 | Theme OFITEC | ✓ | ~ | Básico | Variables primarias aplicadas; pulir layouts. |
|14 | RRHH Avanzado | ~ | ~ | - | Futuro. |
|15 | Compras/Abastecimiento | ~ | ~ | - | Futuro. |
|16 | Mantenimiento | ~ | ~ | - | Futuro. |
|17 | Postventa | ~ | ~ | - | Futuro. |
|18 | Cumplimiento | ~ | ~ | - | Futuro. |
|19 | Portal Cliente | ~ | ~ | - | Futuro. |
|20 | Marketplace/SDK | ~ | ~ | - | Futuro. |

Leyenda: ✓ = sí; ~ = parcial/no.

## 5. Brechas priorizadas (Q3–Q4)
- Tema global: variables de marca (hecho), ordenar assets y refinar componentes KPI y mobile.
- Executive Dashboard: KPIs (margen, días de caja, backlog), anillos y endpoints.
- Presupuestos maestro + carga múltiple.
- Flujo financiero + SII/F29 (API y plan de integración).
- WhatsApp end‑to‑end: webhook, plantillas y métricas.
- Riesgos: matriz P×I y alertas IA.
- DocuChat: indexador Drive/OneDrive + UI.

## 6. PRs sugeridos (lote 1)
- `ofitec_theme`: variables primarias, components, limpieza SCSS, mobile.
- `project_financials`: endpoints KPI + vistas Executive; seed opcional (activado).
- `ofitec_ai_advanced`: separar OWL XML del bundle; consolidar API.
- `ofitec_whatsapp`: webhook + jobs periódicos.
- `project_risk`: matriz y alertas.

## 7. Red flags
- Warnings `tracking` en campos Selection (limpiar CE).
- Ciclos de dependencias (resuelto moviendo Executive a financieros).
- SCSS con `@import` (resuelto) y XML OWL en assets (resuelto quitando del bundle).

## 8. Conclusiones
- Esqueleto presente; tema ya domina marca; falta pulido visual.
- Executive con datos: se creó proyecto + presupuesto + reportes de demo; gráfico operativo.
- Próximos pasos: ejecutar PRs de lote 1 y cerrar brechas UX/IA.

---

## 5. Resultado esperado
- Informe con la tabla completa (✓ / ✗ reemplazando los [ ] según corresponda).  
- Comentarios por módulo sobre:
  - **Completitud** (qué falta).  
  - **Corrección** (qué debe ajustarse).  
  - **Innovación** (si refleja la visión disruptiva o se quedó en lo tradicional).  

---

## 6. Elementos adicionales que debe evaluar Codex
- **Calidad de código**: uso de buenas prácticas en Python, SCSS y XML (nomenclatura clara, modularidad, comentarios).  
- **Consistencia**: que todos los módulos sigan el mismo estándar visual y de arquitectura.  
- **Pruebas**: existencia de tests (unitarios, integración) o al menos hooks para agregarlos.  
- **Seguridad**: validación de accesos y permisos por rol/proyecto.  
- **Extensibilidad**: que la base permita integrar fácilmente los módulos futuros (RH, Mantenimiento, Portal Cliente).  

---

## 7. Anexo: Guía de Auditoría Codex
Al auditar el repo en Visual Studio, revisa en detalle:

*(sección completa con Cobertura de módulos, Flujos críticos, Integraciones, IA, Seguridad, DevOps, Theme, Dashboards BI, Validaciones transversales y Red flags, como fue desarrollado previamente)*

---

## 8. Archivo de salida obligatorio
Codex debe crear y completar el archivo **`codex_auditoria.md`** en la raíz del repo, usando la plantilla ya disponible.  
Ese archivo debe contener:
- Tabla de cobertura con ✓/✗.
- Brechas priorizadas.
- PRs sugeridos.
- Red flags encontrados.
- Conclusiones y recomendaciones.

---

## 9. Nota final
Este proyecto se viene desarrollando por meses y reúne decenas de horas de diseño.  
El **código debe reflejar esa visión**: no basta con que exista el módulo, debe estar implementado de forma **moderna, intuitiva y con IA integrada**.  

Codex: tu misión es asegurarte de que el código en Visual Studio cumple esta visión y entregar un informe claro con observaciones y propuestas de mejora en `codex_auditoria.md`.
