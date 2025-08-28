# Chat del módulo site\_performance

> **Objetivo:** Analizar el desempeño diario de obra comparando avance real vs. plan, productividad de recursos y costos, y generar alertas tempranas de desviaciones.

## Estructura del addon

```
site_performance/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── performance_record.py
│   └── resource_usage.py
├── data/
│   └── ir_cron_performance.xml
├── views/
│   ├── performance_dashboard.xml
│   └── performance_record_views.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    └── test_performance.py
```

---

## 1. **init**.py

```python
# -*- coding: utf-8 -*-
from . import models
```

## 2. **manifest**.py

```python
{
    'name': 'Site Performance',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Análisis de desempeño de obra y alertas de desviaciones',
    'depends': ['site_management', 'project_financials', 'ai_bridge', 'project_risk'],
    'data': [
        'security/ir.model.access.csv',
        'views/performance_record_views.xml',
        'views/performance_dashboard.xml',
        'data/ir_cron_performance.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## 3. Modelos

### models/performance\_record.py

```python
from odoo import models, fields, api
from datetime import date

class PerformanceRecord(models.Model):
    _name = 'site_performance.record'
    _description = 'Registro de Desempeño Diario de Obra'

    project_id = fields.Many2one('project.project', string='Proyecto', required=True)
    date = fields.Date(string='Fecha', default=lambda self: date.today(), required=True)
    planned_progress = fields.Float(string='Avance Plan (%)')
    actual_progress = fields.Float(string='Avance Real (%)')
    deviation = fields.Float(string='Desviación (%)', compute='_compute_deviation', store=True)
    total_cost = fields.Monetary(string='Costo Real', currency_field='company_currency')
    expected_cost = fields.Monetary(string='Costo Estándar', currency_field='company_currency')
    efficiency = fields.Float(string='Eficiencia Recursos', help='Ratio avance vs uso recursos')

    @api.depends('planned_progress', 'actual_progress')
    def _compute_deviation(self):
        for rec in self:
            rec.deviation = rec.actual_progress - rec.planned_progress
```

### models/resource\_usage.py

```python
from odoo import models, fields

class ResourceUsage(models.Model):
    _name = 'site_performance.resource_usage'
    _description = 'Uso de Recursos en Reporte de Desempeño'

    performance_id = fields.Many2one('site_performance.record', string='Desempeño Diario', required=True, ondelete='cascade')
    resource_id = fields.Many2one('site_management.resource', string='Recurso', required=True)
    quantity = fields.Float(string='Cantidad', required=True)
    unit = fields.Selection([('hh','Horas Hombre'),('unit','Unidades'),('m3','Metros³')], default='hh')
```

---

## 4. Data (Cron)

### data/ir\_cron\_performance.xml

```xml
<odoo>
  <record id="ir_cron_compute_performance" model="ir.cron">
    <field name="name">Calcular Desempeño Diario de Obra</field>
    <field name="model_id" ref="model_site_performance_record"/>
    <field name="state">code</field>
    <field name="code">model._cron_compute_performance()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
    <field name="active">True</field>
  </record>
</odoo>
```

---

## 5. Vistas

### views/performance\_record\_views.xml

```xml
<odoo>
  <record id="view_performance_record_tree" model="ir.ui.view">
    <field name="name">site_performance.record.tree</field>
    <field name="model">site_performance.record</field>
    <field name="arch" type="xml">
      <tree>
        <field name="project_id"/>
        <field name="date"/>
        <field name="planned_progress"/>
        <field name="actual_progress"/>
        <field name="deviation"/>
        <field name="efficiency"/>
      </tree>
    </field>
  </record>
  <record id="view_performance_record_form" model="ir.ui.view">
    <field name="name">site_performance.record.form</field>
    <field name="model">site_performance.record</field>
    <field name="arch" type="xml">
      <form>
        <sheet>
          <group>
            <field name="project_id"/>
            <field name="date"/>
            <field name="planned_progress"/>
            <field name="actual_progress"/>
            <field name="deviation"/>
            <field name="total_cost"/>
            <field name="expected_cost"/>
            <field name="efficiency"/>
          </group>
          <group string="Uso de Recursos">
            <field name="resource_usage_ids">
              <tree editable="bottom">
                <field name="resource_id"/>
                <field name="quantity"/>
                <field name="unit"/>
              </tree>
            </field>
          </group>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

### views/performance\_dashboard.xml

```xml
<odoo>
  <record id="action_performance_dashboard" model="ir.actions.act_window">
    <field name="name">Desempeño de Obra</field>
    <field name="res_model">site_performance.record</field>
    <field name="view_mode">graph,tree,form</field>
    <field name="help">Dashboard con gráficos de Curva Plan vs Real y productividad</field>
  </record>

  <menuitem id="menu_site_performance_root" name="Desempeño Obra" sequence="30"/>
  <menuitem id="menu_performance_dashboard" name="Dashboard" parent="menu_site_performance_root" action="action_performance_dashboard"/>
</odoo>
```

---

## 6. Seguridad

### security/ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_performance_record,access_performance_record,model_site_performance_record,base.group_user,1,0,0,0
access_resource_usage,access_resource_usage,model_site_performance_resource_usage,base.group_user,1,1,1,1
```

---

## 7. Tests automáticos

### tests/test\_performance.py

```python
from odoo.tests import TransactionCase

class TestPerformance(TransactionCase):
    def test_compute_deviation(self):
        proj = self.env['project.project'].create({'name': 'Test'})
        rec = self.env['site_performance.record'].create({
            'project_id': proj.id,
            'planned_progress': 50,
            'actual_progress': 40,
        })
        self.assertEqual(rec.deviation, -10)

    def test_cron_creates_records(self):
        # Assumes daily_report exists and flow cron has run
        self.env['site_management.daily_report'].create({
            'project_id': self.env['project.project'].create({'name':'P'}).id,
            'progress': 30,
            'amount_estimated': 300,
        })
        perf = self.env['site_performance.record']
        perf.search([]).unlink()
        self.env['site_performance.record']._cron_compute_performance()
        assert perf.search([]), "Cron de performance no creó registros"
```

