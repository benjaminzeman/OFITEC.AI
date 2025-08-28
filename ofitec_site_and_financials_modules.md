#### Módulo site\_management (Gestión de Obra)

Registra avances y costos diarios de la faena, alimentando el flujo de caja.

```
site_management/
├── __init__.py
├── __manifest__.py
├── models/
│   └── daily_report.py
└── views/
    └── daily_report_views.xml
```

##### **manifest**.py

```python
{
    'name': 'Site Management',
    'version': '1.1',
    'category': 'Project',
    'summary': 'Gestión de reportes diarios de obra',
    'depends': ['project'],
    'data': [
        'views/daily_report_views.xml',
    ],
    'installable': True,
}
```

##### models/daily\_report.py

```python
from odoo import models, fields
from datetime import date

class DailyReport(models.Model):
    _name = 'site_management.daily_report'
    _description = 'Reporte Diario de Avance de Obra'

    project_id = fields.Many2one(
        'project.project', string='Proyecto', required=True,
        ondelete='cascade')
    date = fields.Date(
        string='Fecha', default=lambda self: date.today(), required=True)
    progress = fields.Float(
        string='Avance (%)', help='Porcentaje diario de avance de obra')
    amount_estimated = fields.Monetary(
        string='Costo Estimado', currency_field='company_currency',
        help='Costo estimado de la faena para esta fecha')
    notes = fields.Text(string='Observaciones')
```

##### views/daily\_report\_views.xml

```xml
<odoo>
  <!-- Action -->
  <record id="action_daily_report" model="ir.actions.act_window">
    <field name="name">Reportes Diarios</field>
    <field name="res_model">site_management.daily_report</field>
    <field name="view_mode">tree,form</field>
  </record>

  <!-- Menu -->
  <menuitem id="menu_site_management_root" name="Gestión de Obra" sequence="10"/>
  <menuitem id="menu_daily_report" name="Reportes Diarios"
            parent="menu_site_management_root"
            action="action_daily_report" sequence="20"/>

  <!-- Tree View -->
  <record id="view_daily_report_tree" model="ir.ui.view">
    <field name="name">site_management.daily_report.tree</field>
    <field name="model">site_management.daily_report</field>
    <field name="arch" type="xml">
      <tree string="Reportes Diarios">
        <field name="project_id"/>
        <field name="date"/>
        <field name="progress"/>
        <field name="amount_estimated"/>
      </tree>
    </field>
  </record>

  <!-- Form View -->
  <record id="view_daily_report_form" model="ir.ui.view">
    <field name="name">site_management.daily_report.form</field>
    <field name="model">site_management.daily_report</field>
    <field name="arch" type="xml">
      <form string="Reporte Diario">
        <sheet>
          <group>
            <field name="project_id"/>
            <field name="date"/>
            <field name="progress"/>
            <field name="amount_estimated"/>
          </group>
          <notebook>
            <page string="Observaciones">
              <field name="notes"/>
            </page>
          </notebook>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

