# Chat del módulo flow\_management

> **Objetivo:** Gestionar el flujo de caja y conciliaciones bancarias, centralizando ingresos y egresos, y automatizando la conciliación con extractos bancarios.

## Estructura del addon

```
flow_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── bank_statement.py
│   ├── bank_line.py
│   ├── reconciliation_rule.py
│   └── reconciliation_match.py
├── views/
│   ├── flow_bank_statement_views.xml
│   ├── flow_bank_line_views.xml
│   ├── flow_reconciliation_views.xml
│   └── flow_dashboard_views.xml
├── data/
│   └── ir_cron_reconciliation.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    └── test_flow_management.py
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
    'category': 'Accounting/Reporting',
    'summary': 'Flujo de caja y conciliaciones bancarias',
    'depends': ['account', 'ofitec_cashflow'],
    'data': [
        'security/ir.model.access.csv',
        'views/flow_bank_statement_views.xml',
        'views/flow_bank_line_views.xml',
        'views/flow_reconciliation_views.xml',
        'views/flow_dashboard_views.xml',
        'data/ir_cron_reconciliation.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## 3. Modelos

### models/bank\_statement.py

```python
from odoo import models, fields

class BankStatement(models.Model):
    _name = 'flow_management.bank_statement'
    _description = 'Extracto Bancario'

    name = fields.Char(string='Referencia', required=True)
    date = fields.Date(string='Fecha', required=True)
    statement_line_ids = fields.One2many('flow_management.bank_line', 'statement_id', string='Líneas')
```

### models/bank\_line.py

```python
from odoo import models, fields

class BankLine(models.Model):
    _name = 'flow_management.bank_line'
    _description = 'Línea de Extracto Bancario'

    statement_id = fields.Many2one('flow_management.bank_statement', string='Extracto', required=True, ondelete='cascade')
    date = fields.Date(string='Fecha', required=True)
    description = fields.Char(string='Descripción')
    amount = fields.Monetary(string='Monto', currency_field='company_currency', required=True)
    matched = fields.Boolean(string='Conciliada', default=False)
    reconciliation_match_id = fields.Many2one('flow_management.reconciliation_match', string='Resultado de Conciliación')
```

### models/reconciliation\_rule.py

```python
from odoo import models, fields

class ReconciliationRule(models.Model):
    _name = 'flow_management.reconciliation_rule'
    _description = 'Regla de Conciliación Automática'

    name = fields.Char(string='Nombre', required=True)
    pattern = fields.Char(string='Patrón (Regex)', help='Coincidencia en descripción')
    partner_id = fields.Many2one('res.partner', string='Socio', help='Asignar partner si coincide')
    priority = fields.Integer(string='Prioridad', default=10)
```

### models/reconciliation\_match.py

```python
from odoo import models, fields, api
from datetime import timedelta

class ReconciliationMatch(models.Model):
    _name = 'flow_management.reconciliation_match'
    _description = 'Conciliación de Movimientos'

    line_id = fields.Many2one('flow_management.bank_line', string='Línea Banco', required=True)
    cashflow_id = fields.Many2one('ofitec.cashflow.line', string='Línea de Flujo', required=True)
    rule_id = fields.Many2one('flow_management.reconciliation_rule', string='Regla')
    date = fields.Date(string='Fecha Conciliación', default=fields.Date.today)

    @api.model
    def _cron_auto_reconcile(self):
        rules = self.env['flow_management.reconciliation_rule'].search([], order='priority')
        BankLine = self.env['flow_management.bank_line']
        Cashflow = self.env['ofitec.cashflow.line']
        for line in BankLine.search([('matched','=',False)]):
            for rule in rules:
                if re.search(rule.pattern, line.description or ''):
                    cf = Cashflow.search([('amount','=', abs(line.amount)), ('paid','=',False)], limit=1)
                    if cf:
                        match = self.create({'line_id': line.id, 'cashflow_id': cf.id, 'rule_id': rule.id})
                        line.matched = True
                        cf.paid = True
                        break
```

---

## 4. Vistas

### views/flow\_bank\_statement\_views.xml

```xml
<odoo>
  <record id="view_bank_statement_tree" model="ir.ui.view">
    <field name="name">flow_management.bank_statement.tree</field>
    <field name="model">flow_management.bank_statement</field>
    <field name="arch" type="xml">
      <tree>
        <field name="name"/>
        <field name="date"/>
      </tree>
    </field>
  </record>
  <record id="view_bank_statement_form" model="ir.ui.view">
    <field name="name">flow_management.bank_statement.form</field>
    <field name="model">flow_management.bank_statement</field>
    <field name="arch" type="xml">
      <form>
        <sheet>
          <group>
            <field name="name"/>
            <field name="date"/>
          </group>
          <notebook>
            <page string="Líneas">
              <field name="statement_line_ids">
                <tree editable="bottom">
                  <field name="date"/>
                  <field name="description"/>
                  <field name="amount"/>
                  <field name="matched"/>
                </tree>
              </field>
            </page>
          </notebook>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

### views/flow\_reconciliation\_views.xml

```xml
<odoo>
  <record id="view_reconciliation_rule_tree" model="ir.ui.view">
    <field name="name">flow_management.reconciliation_rule.tree</field>
    <field name="model">flow_management.reconciliation_rule</field>
    <field name="arch" type="xml">
      <tree>
        <field name="name"/>
        <field name="pattern"/>
        <field name="partner_id"/>
      </tree>
    </field>
  </record>
</odoo>
```

### views/flow\_dashboard\_views.xml

```xml
<odoo>
  <record id="action_flow_dashboard" model="ir.actions.act_window">
    <field name="name">Dashboard Flujo de Caja</field>
    <field name="res_model">ofitec.cashflow.line</field>
    <field name="view_mode">kanban,tree,form</field>
    <field name="help">Resumen de estados y partidas pendientes de conciliación.</field>
  </record>
  <menuitem id="menu_flow_dashboard" name="Flujo de Caja" sequence="40"/>
  <menuitem id="menu_flow_dashboard_view" name="Dashboard" parent="menu_flow_dashboard" action="action_flow_dashboard"/>
</odoo>
```

---

## 5. Data (Cron de conciliación)

### data/ir\_cron\_reconciliation.xml

```xml
<odoo>
  <record id="ir_cron_auto_reconcile" model="ir.cron">
    <field name="name">Conciliación Automática</field>
    <field name="model_id" ref="model_flow_management_reconciliation_match"/>
    <field name="state">code</field>
    <field name="code">model._cron_auto_reconcile()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">hours</field>
    <field name="active">True</field>
  </record>
</odoo>
```

---

## 6. Seguridad

### security/ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_bank_statement,access_bank_statement,model_flow_management_bank_statement,base.group_user,1,1,1,1
access_bank_line,access_bank_line,model_flow_management_bank_line,base.group_user,1,1,1,1
access_reconciliation_rule,access_reconciliation_rule,model_flow_management_reconciliation_rule,base.group_user,1,1,1,1
access_reconciliation_match,access_reconciliation_match,model_flow_management_reconciliation_match,base.group_user,1,1,1,1
```

---

## 7. Tests automáticos

### tests/test\_flow\_management.py

```python
from odoo.tests import TransactionCase

class TestFlowManagement(TransactionCase):
    def test_bank_statement_creation(self):
        stmt = self.env['flow_management.bank_statement'].create({
            'name': 'Extracto 001',
            'date': '2025-08-06'
        })
        self.assertTrue(stmt)

    def test_auto_reconcile(self):
        # Crear regla simple
        rule = self.env['flow_management.reconciliation_rule'].create({
            'name': 'Test Rule',
            'pattern': 'Pago Factura',
            'priority': 1
        })
        # Crear línea banco
        line = self.env['flow_management.bank_line'].create({
            'statement_id': self.env['flow_management.bank_statement'].create({'name':'S','date':'2025-08-06'}).id,
            'date': '2025-08-06',
            'description': 'Pago Factura',
            'amount': 100.0
        })
        # Crear línea cashflow
        cf = self.env['ofitec.cashflow.line'].create({
            'project_id': self.env['project.project'].create({'name':'P'}).id,
            'name': 'Test',
            'date_start': '2025-08-06',
            'amount': 100.0
        })
        # Limpiar matches previos
        self.env['flow_management.reconciliation_match'].search([]).unlink()
        line.write({'matched': False})
        # Ejecutar cron
        self.env['flow_management.reconciliation_match']._cron_auto_reconcile()
        # Verificar match
        match = self.env['flow_management.reconciliation_match'].search([('line_id','=',line.id)])
        self.assertTrue(match)
```

