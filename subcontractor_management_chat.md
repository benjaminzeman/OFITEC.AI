# 🗂 Chat del módulo subcontractor\_management

> **Objetivo:** Gestionar subcontratistas con detalle de contratos, avances, pagos, hitos y alertas, integrándose con el flujo de caja, project\_management y reportes de obra.

## 1. Estructura del addon

```
subcontractor_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── subcontractor.py
│   ├── contract.py
│   ├── progress_entry.py
│   └── payment.py
├── views/
│   ├── subcontractor_views.xml
│   ├── contract_views.xml
│   └── dashboard_templates.xml
├── data/
│   ├── ir_cron_monitoring.xml
│   └── subcontractor_menu.xml
├── security/
│   ├── ir.model.access.csv
│   └── subcontractor_security.xml
└── tests/
    ├── test_subcontractor.py
    └── test_payments.py
```

## 2. **manifest**.py

```python
{
    'name': 'Subcontractor Management',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Control completo de subcontratistas: contratos, avances y pagos',
    'depends': ['project', 'site_management', 'flow_management
- **bank_connector_openbanking**: Importación de extractos bancarios (manual OFX/CSV, SFTP, Open Banking BCI/Santander)
- **site_performance**: KPIs y alertas de rendimiento de obra
- **subcontractor_management**: Gestión integral de subcontratistas, contratos, avances y pagos', 'ofitec_theme'],
    'data': [
        'security/ir.model.access.csv',
        'security/subcontractor_security.xml',
        'data/subcontractor_menu.xml',
        'data/ir_cron_monitoring.xml',
        'views/subcontractor_views.xml',
        'views/contract_views.xml',
        'views/dashboard_templates.xml',
    ],
    'installable': True,
    'application': False,
}
```

## 3. Modelos

### 3.1 subcontractor.py

```python
from odoo import models, fields

class Subcontractor(models.Model):
    _name = 'subcontractor.management'
    _description = 'Subcontratista'

    name = fields.Char(string='Nombre', required=True)
    specialty = fields.Char(string='Especialidad')
    active_projects = fields.One2many('project.project', 'subcontractor_id', string='Proyectos Activos')
    contract_ids = fields.One2many('subcontractor.contract', 'subcontractor_id', string='Contratos')
    rate_type = fields.Selection([('unit','Por unidad'),('hour','Por hora'),('milestone','Por hito')], default='hour')
    notes = fields.Text(string='Notas y condiciones')
```

### 3.2 contract.py

```python
from odoo import models, fields, api

class SubcontractorContract(models.Model):
    _name = 'subcontractor.contract'
    _description = 'Contrato de Subcontratista'

    name = fields.Char(string='Código', required=True)
    subcontractor_id = fields.Many2one('subcontractor.management', string='Subcontratista', required=True)
    project_id = fields.Many2one('project.project', string='Proyecto', required=True)
    date_start = fields.Date(string='Fecha Inicio', required=True)
    date_end = fields.Date(string='Fecha Término')
    amount = fields.Monetary(string='Monto Total', currency_field='company_currency')
    state = fields.Selection([('draft','Borrador'),('active','Activo'),('done','Finalizado')], default='draft')

    @api.model
def action_activate(self):
        self.state = 'active'

    @api.model
def action_close(self):
        self.state = 'done'
```

### 3.3 progress\_entry.py

```python
from odoo import models, fields, api

class ProgressEntry(models.Model):
    _name = 'subcontractor.progress_entry'
    _description = 'Avance de Subcontratista'

    contract_id = fields.Many2one('subcontractor.contract', string='Contrato', required=True)
    date = fields.Date(string='Fecha', default=fields.Date.today(), required=True)
    description = fields.Text(string='Descripción de la Avance')
    quantity = fields.Float(string='Cantidad (unidades/horas)')
    amount = fields.Monetary(string='Costo', currency_field='company_currency')

    @api.model
def create(self, vals):
        rec = super().create(vals)
        # Integrar con flujo de caja
        self.env['flow_management.cashflow_line'].create({
            'project_id': rec.contract_id.project_id.id,
            'date_start': rec.date,
            'amount': rec.amount,
            'category': 'other',
            'description': f"Avance subcontractor {rec.contract_id.name}",
            'other_id': rec.id,
        })
        return rec
```

#### 3.4 payment.py

```python
from odoo import models, fields, api

class SubcontractorPayment(models.Model):
    _name = 'subcontractor.payment'
    _description = 'Pago a Subcontratista'

    contract_id = fields.Many2one('subcontractor.contract', string='Contrato', required=True)
    date = fields.Date(string='Fecha de Pago', default=fields.Date.today(), required=True)
    amount = fields.Monetary(string='Monto Pagado', currency_field='company_currency')
    bank_line_id = fields.Many2one('account.bank.statement.line', string='Línea Bancaria')

    @api.model
def action_conciliate(self):
        # Asocia con flujo y marca línea bancaria
        for rec in self:
            line = rec.bank_line_id
            cf_line = self.env['flow_management.cashflow_line'].search([
                ('other_id','=', rec.id),
                ('category','=','other')
            ], limit=1)
            if cf_line:
                line.write({'cashflow_line_id': cf_line.id})
        return True
```

---

## 8. Código de UI para Subcontratistas y Contratos

Para reflejar la nueva UI, incluimos vistas Kanban y Gantt.

### 8.1 subcontractor\_views.xml

```xml
<odoo>
  <record id="view_subcontractor_kanban" model="ir.ui.view">
    <field name="name">subcontractor.management.kanban</field>
    <field name="model">subcontractor.management</field>
    <field name="arch" type="xml">
      <kanban default_group_by="state" class="o_subc_kanban">
        <templates>
          <t t-name="kanban-box">
            <div t-attf-class="oe_kanban_card badge-#{record.state.raw_value}">
              <div class="o_badge"><field name="state"/></div>
              <strong><field name="name"/></strong>
              <div><small>Contratos: <t t-esc="record.contract_ids.raw_value.length"/></small></div>
              <div><small>Pagos: <t t-esc="record._compute_payment_pct()"/>%</small></div>
            </div>
          </t>
        </templates>
      </kanban>
    </field>
  </record>

  <record id="action_subcontractor_kanban" model="ir.actions.act_window">
    <field name="name">Subcontratistas</field>
    <field name="res_model">subcontractor.management</field>
    <field name="view_mode">kanban,tree,form</field>
  </record>
</odoo>
```

### 8.2 contract\_views.xml

```xml
<odoo>
  <record id="view_contract_gantt" model="ir.ui.view">
    <field name="name">subcontractor.contract.gantt</field>
    <field name="model">subcontractor.contract</field>
    <field name="arch" type="xml">
      <gantt date_start="date_start"
             date_stop="date_end"
             default_group_by="project_id"
             color="state">       
        <field name="project_id"/>
        <field name="name"/>
        <field name="state"/>
      </gantt>
    </field>
  </record>

  <record id="action_contract_gantt" model="ir.actions.act_window">
    <field name="name">Contratos</field>
    <field name="res_model">subcontractor.contract</field>
    <field name="view_mode">gantt,tree,form</field>
  </record>
</odoo>
```

### 8.3 quick\_progress\_wizard.py

```python
from odoo import models, fields, api

class QuickProgressWizard(models.TransientModel):
    _name = 'subcontractor.quick_progress_wizard'
    _description = 'Wizard de registro rápido de avance'

    contract_id = fields.Many2one('subcontractor.contract', string='Contrato', required=True)
    date = fields.Date(string='Fecha', default=fields.Date.today(), required=True)
    quantity = fields.Float(string='Cantidad', required=True)
    amount = fields.Monetary(string='Monto', currency_field='company_currency', required=True)
    conciliate = fields.Boolean(string='Conciliar con banco', default=True)

    @api.model
def action_submit(self):
        wizard = self
        # Crear progress entry
        pe = self.env['subcontractor.progress_entry'].create({
            'contract_id': wizard.contract_id.id,
            'date': wizard.date,
            'quantity': wizard.quantity,
            'amount': wizard.amount,
        })
        if wizard.conciliate:
            # Lógica para sugerir partida bancaria (mock)
            pass
        return {'type': 'ir.actions.act_window_close'}
```

### 8.4 quick\_progress\_wizard\_views.xml

```xml
<odoo>
  <record id="view_quick_progress_wizard" model="ir.ui.view">
    <field name="name">quick.progress.wizard.form</field>
    <field name="model">subcontractor.quick_progress_wizard</field>
    <field name="arch" type="xml">
      <form string="Registro Rápido de Avance">
        <sheet>
          <group>
            <field name="contract_id"/>
            <field name="date"/>
            <field name="quantity"/>
            <field name="amount"/>
            <field name="conciliate"/>
          </group>
          <footer>
            <button string="Registrar" type="object" name="action_submit" class="btn-primary"/>
            <button string="Cancelar" class="btn-secondary" special="cancel"/>
          </footer>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

## 9. Menú de Wizard

Agregar en `subcontractor_menu.xml`:

```xml
<odoo>
  <menuitem id="menu_subcontractor_root" name="Subcontratistas" sequence="10"/>
  <menuitem id="menu_subcontractor_wizard" name="Registro Rápido Avance"
            parent="menu_subcontractor_root"
            action="subcontractor.quick_progress_wizard_action"/>

  <record id="subcontractor.quick_progress_wizard_action" model="ir.actions.act_window">
    <field name="name">Avance Rápido</field>
    <field name="res_model">subcontractor.quick_progress_wizard</field>
    <field name="view_mode">form</field>
    <field name="target">new</field>
  </record>
</odoo>
```

---

Con estos archivos, el usuario dispondrá de:

- **Kanban** dinámico para ver subcontratistas y su estado.
- **Gantt** interactivo para gestión de contratos.
- **Wizard modal** para registro rápido de avances y opción de conciliación.

Y todo respetando la consideración de que un subcontratista puede tener múltiples proyectos simultáneos.

