# Chat del módulo flow\_management

> **Objetivo:** Gestionar flujos de caja, conciliación bancaria y alertas automáticas de partidas pendientes.

## Estructura del addon

```
flow_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── cashflow_line.py
│   └── conciliation_rule.py
├── views/
│   ├── cashflow_views.xml
│   └── conciliation_views.xml
├── data/
│   └── ir_cron_cashflow.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    ├── test_cashflow.py
    └── test_conciliation.py
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
    'name': 'Flow Management',
    'version': '16.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Flujo de Caja Semanal y Conciliación Bancaria',
    'depends': ['account', 'purchase', 'flow_management', 'site_management', 'project_financials'],
    'data': [
        'security/ir.model.access.csv',
        'views/cashflow_views.xml',
        'views/conciliation_views.xml',
        'data/ir_cron_cashflow.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## 3. Modelos

### models/cashflow\_line.py

```python
from odoo import models, fields, api
from datetime import timedelta

class CashflowLine(models.Model):
    _name = 'flow_management.cashflow_line'
    _description = 'Línea de Flujo de Caja'

    project_id = fields.Many2one('project.project', string='Proyecto', required=True)
    date_start = fields.Date(string='Semana Inicio', required=True)
    date_end = fields.Date(string='Semana Fin', compute='_compute_date_end', store=True)
    amount = fields.Monetary(string='Monto', currency_field='company_currency')
    category = fields.Selection([
        ('budget','Presupuesto'), ('purchase','Orden de Compra'),
        ('invoice','Factura'), ('labor','Mano de Obra'),
        ('daily','Reporte Diario'), ('other','Otro')
    ], string='Tipo', required=True)
    paid = fields.Boolean(string='Pagado')
    daily_report_id = fields.Many2one('site_management.daily_report', string='Reporte Diario')
    budget_id = fields.Many2one('project_financials.project_budget', string='Presupuesto')
    purchase_order_id = fields.Many2one('purchase.order', string='OC')
    invoice_id = fields.Many2one('account.move', string='Factura')
    # compute date_end
    @api.depends('date_start')
    def _compute_date_end(self):
        for rec in self:
            if rec.date_start:
                rec.date_end = rec.date_start + timedelta(days=6)

    @api.model
def _cron_generate_cashflow(self):
        # Simplified: upsert lines from daily reports
        for dr in self.env['site_management.daily_report'].search([]):
            vals = {
                'project_id': dr.project_id.id,
                'date_start': dr.date,
                'amount': dr.amount_estimated,
                'category': 'daily',
                'daily_report_id': dr.id,
            }
            self._upsert(vals)

    def _upsert(self, vals):
        line = self.search([('daily_report_id','=', vals.get('daily_report_id'))], limit=1)
        if line:
            line.write(vals)
        else:
            self.create(vals)
```

### models/conciliation\_rule.py

```python
from odoo import models, fields

class ConciliationRule(models.Model):
    _name = 'flow_management.conciliation_rule'
    _description = 'Regla de Conciliación Bancaria'

    name = fields.Char(string='Nombre', required=True)
    pattern = fields.Char(string='Regex', help='Expresión regular para emparejar concepto bancario')
    partner_id = fields.Many2one('res.partner', string='Partner Asociado')

    def match_move(self, bank_line):
        import re
        for rule in self.search([]):
            if re.search(rule.pattern, bank_line.name or ''):
                return rule.partner_id
        return None
```

---

## 4. Vistas

### views/cashflow\_views.xml

```xml
<odoo>
  <record id="view_cashflow_tree" model="ir.ui.view">
    <field name="name">flow_management.cashflow_line.tree</field>
    <field name="model">flow_management.cashflow_line</field>
    <field name="arch" type="xml">
      <tree>
        <field name="project_id"/>
        <field name="date_start"/>
        <field name="amount"/>
        <field name="category"/>
        <field name="paid"/>
      </tree>
    </field>
  </record>
</odoo>
```

### views/conciliation\_views.xml

```xml
<odoo>
  <record id="view_conciliation_rule_tree" model="ir.ui.view">
    <field name="name">flow_management.conciliation_rule.tree</field>
    <field name="model">flow_management.conciliation_rule</field>
    <field name="arch" type="xml">
      <tree>
        <field name="name"/>
        <field name="pattern"/>
        <field name="partner_id"/>
      </tree>
    </field>
  </record>
  <record id="view_conciliation_rule_form" model="ir.ui.view">
    <field name="name">flow_management.conciliation_rule.form</field>
    <field name="model">flow_management.conciliation_rule</field>
    <field name="arch" type="xml">
      <form>
        <sheet>
          <group>
            <field name="name"/>
            <field name="pattern"/>
            <field name="partner_id"/>
          </group>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

---

## 5. Data (Cron Job)

### data/ir\_cron\_cashflow\.xml

```xml
<odoo>
  <record id="ir_cron_cashflow_update" model="ir.cron">
    <field name="name">Actualizar Flujo de Caja</field>
    <field name="model_id" ref="model_flow_management_cashflow_line"/>
    <field name="state">code</field>
    <field name="code">model._cron_generate_cashflow()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">weeks</field>
    <field name="active">True</field>
  </record>
</odoo>
```

---

## 6. Seguridad

### security/ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_cashflow_line,access_cashflow_line,model_flow_management_cashflow_line,base.group_user,1,1,1,1
access_conciliation_rule,access_conciliation_rule,model_flow_management_conciliation_rule,base.group_user,1,1,1,1
```

---

## 7. Tests automáticos

### tests/test\_cashflow\.py

```python
from odoo.tests import TransactionCase
from datetime import date

class TestCashflow(TransactionCase):
    def test_compute_date_end(self):
        line = self.env['flow_management.cashflow_line'].create({
            'project_id': self.env['project.project'].create({'name':'P'}).id,
            'date_start': '2025-08-01',
            'amount': 100.0,
            'category': 'daily'
        })
        self.assertEqual(line.date_end.strftime('%Y-%m-%d'), '2025-08-07')

    def test_cron_generate_cashflow(self):
        # Create daily report
        dr = self.env['site_management.daily_report'].create({
            'project_id': self.env['project.project'].create({'name':'P2'}).id,
            'progress': 10,
            'amount_estimated': 200
        })
        # Clear existing lines
        self.env['flow_management.cashflow_line'].search([]).unlink()
        self.env['flow_management.cashflow_line']._cron_generate_cashflow()
        lines = self.env['flow_management.cashflow_line'].search([('daily_report_id','=',dr.id)])
        assert lines, 'Cron no creó líneas de cashflow'
```

### tests/test\_conciliation.py

```python
from odoo.tests import TransactionCase

class TestConciliation(TransactionCase):
    def test_rule_match(self):
        partner = self.env['res.partner'].create({'name':'Test'})
        rule = self.env['flow_management.conciliation_rule'].create({
            'name': 'Test Rule',
            'pattern': 'TEST',
            'partner_id': partner.id
        })
        # Simulate bank line
        bank_line = type('BankLine', (), {'name': 'Pago TEST 123'})
        matched = rule.match_move(bank_line)
        self.assertEqual(matched.id, partner.id)
```

