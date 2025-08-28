#### Estructura del módulo ofitec\_cashflow

```
ofitec_cashflow/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── ir_cron.xml
│   ├── ir_cron_kpi.xml
│   └── ir_cron_site.xml
├── models/
│   ├── __init__.py
│   ├── cashflow_line.py
│   └── cashflow_kpi.py
└── views/
    └── cashflow_views.xml
```

---

##### **init**.py

```python
from . import models
```

##### **manifest**.py

```python
{
    "name": "Cashflow Semanal Interactivo",
    "version": "1.5",
    "category": "Accounting/Reporting",
    "summary": "Flujo de caja semanal interactivo con integración de obra y finanzas",
    "description": "Gestiona proyecciones, compromisos, ingresos, nómina, impuestos, obra y presupuestos en un tablero arrastrable con KPIs y alertas.",
    "author": "Tu Nombre",
    "depends": [
        "project",
        "purchase",
        "account",
        "sale_management",
        "hr_payroll_account_move",
        "l10n_cl_edi",
        "site_management",
        "project_financials"
    ],
    "data": [
        "data/ir_cron.xml",
        "data/ir_cron_kpi.xml",
        "data/ir_cron_site.xml",
        "views/cashflow_views.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
```

##### data/ir\_cron\_site.xml

```xml
<odoo>
  <record id="ir_cron_site_cashflow" model="ir.cron">
    <field name="name">Actualizar Cashflow desde Obra y Presupuestos</field>
    <field name="model_id" ref="model_ofitec_cashflow_line"/>
    <field name="state">code</field>
    <field name="code">model._cron_generate_site_and_budget()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
    <field name="active">True</field>
  </record>
</odoo>
```

##### models/cashflow\_line.py

```python
from odoo import models, fields, api
from datetime import timedelta

class CashflowLine(models.Model):
    _name = 'ofitec.cashflow.line'
    _description = 'Línea de Flujo de Caja Semanal'

    project_id = fields.Many2one('project.project', string='Obra/Proyecto', required=True)
    name = fields.Char(string='Descripción', required=True)
    category = fields.Selection([
        ('budget', 'Proyección'),
        ('purchase', 'Orden de Compra'),
        ('invoice', 'Factura'),
        ('labor', 'Mano de obra'),
        ('material', 'Materiales'),
        ('sale_order', 'Orden de Venta'),
        ('sale_invoice', 'Factura de Venta'),
        ('tax', 'Impuesto'),
        ('daily', 'Reporte Diario'),
        ('change', 'Orden de Cambio'),
        ('other', 'Otro')
    ], string='Tipo', default='invoice')
    date_start = fields.Date(string='Semana (inicio)', required=True)
    date_end = fields.Date(string='Fin de semana', compute='_compute_date_end', store=True)
    amount = fields.Monetary(string='Monto proyectado', currency_field='company_currency')
    paid = fields.Boolean(string='Pagado', default=False)
    theoretical = fields.Boolean(string='Teórico')

    # Integraciones
    purchase_order_id = fields.Many2one('purchase.order', string='OC')
    invoice_id = fields.Many2one('account.move', string='Factura Compra', domain=[('move_type','in',['in_invoice','in_receipt'])])
    sale_order_id = fields.Many2one('sale.order', string='OV')
    sale_invoice_id = fields.Many2one('account.move', string='Factura Venta', domain=[('move_type','in',['out_invoice'])])
    payslip_id = fields.Many2one('hr.payslip', string='Nómina')
    tax_move_id = fields.Many2one('account.move', string='Impuesto DTE')
    daily_report_id = fields.Many2one('site_management.daily_report', string='Reporte Diario')
    change_order_id = fields.Many2one('project_financials.change_order', string='Orden de Cambio')
    budget_id = fields.Many2one('project_financials.project_budget', string='Presupuesto')

    @api.depends('date_start')
    def _compute_date_end(self):
        for rec in self:
            rec.date_end = rec.date_start + timedelta(days=6)

    def _upsert_line(self, record, category, link_field, date_field, amount_field):
        date = getattr(record, date_field, False)
        if not date:
            return
        week_start = date - timedelta(days=date.weekday())
        vals = {
            'project_id': record.project_id.id,
            'name': record.name or record.display_name,
            'category': category,
            'date_start': week_start,
            'amount': getattr(record, amount_field, 0.0),
            link_field: record.id,
        }
        domain = [(link_field, '=', record.id)]
        existing = self.search(domain)
        if existing:
            existing.write(vals)
        else:
            self.create(vals)

    @api.model
    def _cron_generate_site_and_budget(self):
        # Reportes diarios
        reports = self.env['site_management.daily_report'].search([])
        for rep in reports:
            self._upsert_line(rep, 'daily', 'daily_report_id', 'date', 'amount_estimated')
        # Órdenes de cambio
        changes = self.env['project_financials.change_order'].search([])
        for ch in changes:
            self._upsert_line(ch, 'change', 'change_order_id', 'date', 'amount')
        # Presupuestos teóricos
        budgets = self.env['project_financials.project_budget'].search([])
        for bud in budgets:
            self._upsert_line(bud, 'budget', 'budget_id', 'start_date', 'planned_amount')
```

##### models/cashflow\_kpi.py

```python
# (sin cambios)
```

##### views/cashflow\_views.xml

```xml
<!-- Añade filtros por Reporte Diario, Orden de Cambio y Presupuesto -->
<filter name="daily" string="Reportes Diarios" domain="[('category','=','daily')]"/>
<filter name="change" string="Órdenes de Cambio" domain="[('category','=','change')]"/>
<filter name="budget" string="Presupuestos" domain="[('category','=','budget')]"/>
```

