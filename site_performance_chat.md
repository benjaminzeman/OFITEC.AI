# 🗂 Chat del módulo site\_performance

> **Objetivo:** Consolidar datos de avance diario, uso de recursos y costes para generar KPIs, reportes y alertas de rendimiento de obra.

## 1. Estructura del addon

```
site_performance/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── performance_record.py
│   └── crons.py
├── views/
│   ├── performance_views.xml
│   └── dashboard_templates.xml
├── data/
│   └── ir_cron_performance.xml
├── security/
│   ├── ir.model.access.csv
│   └── performance_security.xml
└── tests/
    ├── test_performance.py
    └── test_alerts.py
```

## 2. **manifest**.py

```python
{
    'name': 'Site Performance',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'KPIs, reportes y alertas de rendimiento de obra',
    'depends': ['site_management', 'flow_management', 'ofitec_theme'],
    'data': [
        'security/ir.model.access.csv',
        'security/performance_security.xml',
        'data/ir_cron_performance.xml',
        'views/performance_views.xml',
        'views/dashboard_templates.xml',
    ],
    'installable': True,
    'application': False,
}
```

## 3. Modelos

### 3.1 performance\_record.py

```python
from odoo import models, fields, api
from datetime import timedelta

class PerformanceRecord(models.Model):
    _name = 'site_performance.performance_record'
    _description = 'Indicador de Rendimiento de Obra'

    project_id = fields.Many2one('project.project', string='Proyecto', required=True)
    date = fields.Date(string='Fecha', required=True)
    progress_pct = fields.Float(string='Avance (%)')
    cost_incurred = fields.Monetary(string='Costo Realizado', currency_field='company_currency')
    cost_planned = fields.Monetary(string='Costo Planificado', currency_field='company_currency')
    resource_usage = fields.Float(string='HH Equivalentes')
    deviation = fields.Float(string='Desviación (%)', compute='_compute_deviation')

    @api.depends('progress_pct','cost_incurred','cost_planned')
    def _compute_deviation(self):
        for rec in self:
            rec.deviation = 0.0
            if rec.cost_planned:
                rec.deviation = (rec.cost_incurred - rec.cost_planned) / rec.cost_planned * 100
```

### 3.2 crons.py

```python
from odoo import models, api
from datetime import date

class PerformanceCron(models.Model):
    _name = 'site_performance.cron'
    _description = 'Crons de Performance'

    @api.model
    def _cron_generate_performance(self):
        # Extraer avances diarios y presupuestos desde site_management y project_financials
        reports = self.env['site_management.daily_report'].search([('date','=',date.today())])
        for dr in reports:
            # Buscar presupuestado en misma fecha
            budget = self.env['project_financials.project_budget'].search([
                ('project_id','=',dr.project_id.id),
                ('start_date','<=', dr.date),
            ], order='start_date desc', limit=1)
            self.env['site_performance.performance_record'].create({
                'project_id': dr.project_id.id,
                'date': dr.date,
                'progress_pct': dr.progress,
                'cost_incurred': dr.amount_estimated,
                'cost_planned': budget.planned_amount if budget else 0,
                'resource_usage': dr.progress * dr.amount_estimated / 100,
            })
```

## 4. Vistas

### performance\_views.xml

- Tree y Form para `performance_record`, con filtros por proyecto y rango de fechas.

### dashboard\_templates.xml

- OWL component que renderiza gráficos de líneas (S-curve) y barras de desviación.
- Incluye un template `<div id="performance_dashboard"></div>` y script JS para cargar datos via RPC.

## 5. Data (Cron)

### ir\_cron\_performance.xml

```xml
<odoo>
  <record id="ir_cron_generate_performance" model="ir.cron">
    <field name="name">Generar KPIs de Performance</field>
    <field name="model_id" ref="model_site_performance_cron"/>
    <field name="state">code</field>
    <field name="code">model._cron_generate_performance()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
    <field name="active">True</field>
  </record>
</odoo>
```

## 6. Seguridad

- `ir.model.access.csv` con roles `project_manager`, `supervisor`, `gerente`.
- `performance_security.xml` define grupos y reglas de acceso.

## 7. Tests Básicos

- `tests/test_performance.py`: verificar cálculo de desviación.
- `tests/test_alerts.py`: simular registro fuera de umbral y creación de alerta.

---

**Nota:** La capa estética (colores, tipografías, cards) se toma de `ofitec_theme` para asegurar consistencia visual en dashboard y formularios.

