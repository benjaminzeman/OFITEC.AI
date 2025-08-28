# Chat del módulo project\_financials

> **Objetivo:** Gestionar presupuestos y órdenes de cambio de proyectos, proporcionando vistas intuitivas y asegurando la correcta captura de la información clave.

## Estructura del addon

```
project_financials/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── project_budget.py
│   └── change_order.py
├── views/
│   ├── project_budget_views.xml
│   └── change_order_views.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    └── test_project_financials.py
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
    'name': 'Project Financials',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Project',
    'summary': 'Presupuestos y órdenes de cambio de proyectos',
    'depends': ['project', 'account', 'ofitec_cashflow'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_budget_views.xml',
        'views/change_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## 3. Modelos

### models/project\_budget.py

```python
from odoo import models, fields

class ProjectBudget(models.Model):
    _name = 'project_financials.project_budget'
    _description = 'Presupuesto de Proyecto'

    project_id = fields.Many2one(
        'project.project', string='Proyecto', required=True,
        ondelete='cascade')
    start_date = fields.Date(
        string='Fecha Inicio', required=True)
    planned_amount = fields.Monetary(
        string='Monto Planificado', currency_field='company_currency',
        required=True)
    description = fields.Text(
        string='Descripción')
```

### models/change\_order.py

```python
from odoo import models, fields

class ChangeOrder(models.Model):
    _name = 'project_financials.change_order'
    _description = 'Orden de Cambio de Proyecto'

    project_id = fields.Many2one(
        'project.project', string='Proyecto', required=True,
        ondelete='cascade')
    date = fields.Date(
        string='Fecha', required=True)
    amount = fields.Monetary(
        string='Monto Ajuste', currency_field='company_currency',
        required=True)
    reason = fields.Text(
        string='Motivo del Cambio')
```

---

## 4. Vistas

### 4.1. Presupuestos (`views/project_budget_views.xml`)

```xml
<odoo>
  <record id="view_project_budget_tree" model="ir.ui.view">
    <field name="name">project_financials.project_budget.tree</field>
    <field name="model">project_financials.project_budget</field>
    <field name="arch" type="xml">
      <tree string="Presupuestos de Proyecto">
        <field name="project_id"/>
        <field name="start_date"/>
        <field name="planned_amount"/>
      </tree>
    </field>
  </record>
  <record id="view_project_budget_form" model="ir.ui.view">
    <field name="name">project_financials.project_budget.form</field>
    <field name="model">project_financials.project_budget</field>
    <field name="arch" type="xml">
      <form string="Presupuesto de Proyecto">
        <sheet>
          <group>
            <field name="project_id"/>
            <field name="start_date"/>
            <field name="planned_amount"/>
            <field name="description"/>
          </group>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

### 4.2. Órdenes de Cambio (`views/change_order_views.xml`)

```xml
<odoo>
  <record id="view_change_order_tree" model="ir.ui.view">
    <field name="name">project_financials.change_order.tree</field>
    <field name="model">project_financials.change_order</field>
    <field name="arch" type="xml">
      <tree string="Órdenes de Cambio">
        <field name="project_id"/>
        <field name="date"/>
        <field name="amount"/>
      </tree>
    </field>
  </record>
  <record id="view_change_order_form" model="ir.ui.view">
    <field name="name">project_financials.change_order.form</field>
    <field name="model">project_financials.change_order</field>
    <field name="arch" type="xml">
      <form string="Orden de Cambio de Proyecto">
        <sheet>
          <group>
            <field name="project_id"/>
            <field name="date"/>
            <field name="amount"/>
            <field name="reason"/>
          </group>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

---

## 5. Seguridad

### security/ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_project_budget,access_project_budget,model_project_financials_project_budget,base.group_user,1,1,1,1
access_change_order,access_change_order,model_project_financials_change_order,base.group_user,1,1,1,1
```

---

## 6. Tests automáticos

### tests/test\_project\_financials.py

```python
from odoo.tests import TransactionCase

class TestProjectFinancials(TransactionCase):
    def test_project_budget_fields(self):
        proj = self.env['project.project'].create({'name': 'TestProj'})
        budget = self.env['project_financials.project_budget'].create({
            'project_id': proj.id,
            'start_date': '2025-08-06',
            'planned_amount': 5000.0,
            'description': 'Test budget'
        })
        self.assertEqual(budget.project_id.id, proj.id)
        self.assertEqual(budget.planned_amount, 5000.0)

    def test_change_order_fields(self):
        proj = self.env['project.project'].create({'name': 'TestProj2'})
        change = self.env['project_financials.change_order'].create({
            'project_id': proj.id,
            'date': '2025-08-07',
            'amount': 200.0,
            'reason': 'Test change'
        })
        self.assertEqual(change.reason, 'Test change')
        self.assertEqual(change.amount, 200.0)
```

