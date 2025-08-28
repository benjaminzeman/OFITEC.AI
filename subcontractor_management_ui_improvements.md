# 🗂 Chat del módulo subcontractor\_management (UI/UX Mejorada)

> **Objetivo:** Diseñar e implementar las mejoras UX/UI para el módulo de gestión de subcontratistas: Kanban, Wizard de contratos, dashboard de performance, formularios tabulados, toasts y mobile-first.

## 1. Vista Kanban de Subcontratistas

```xml
<odoo>
  <record id="view_subcontractor_kanban" model="ir.ui.view">
    <field name="name">subcontractor_management.subcontractor.kanban</field>
    <field name="model">subcontractor_management.subcontractor</field>
    <field name="arch" type="xml">
      <kanban>
        <templates>
          <t t-name="kanban-box">
            <div class="oe_kanban_card oe_kanban_global_click">
              <strong><field name="name"/></strong>
              <div><field name="specialty"/></div>
              <div class="o_badge bg-info">
                <field name="active_projects_count"/>&nbsp;proyectos activos
              </div>
            </div>
          </t>
        </templates>
      </kanban>
    </field>
  </record>

  <record id="action_subcontractor_kanban" model="ir.actions.act_window">
    <field name="name">Subcontratistas</field>
    <field name="res_model">subcontractor_management.subcontractor</field>
    <field name="view_mode">kanban,tree,form</field>
  </record>
</odoo>
```

## 2. Wizard de Alta de Contrato

```python
# models/contract_wizard.py
from odoo import models, fields, api

class ContractWizard(models.TransientModel):
    _name = 'subcontractor_management.contract_wizard'
    _description = 'Wizard Alta de Contrato Subcontratista'

    subcontractor_id = fields.Many2one('subcontractor_management.subcontractor', required=True)
    project_id       = fields.Many2one('project.project', required=True)
    contract_type    = fields.Selection([('unit','Por unidad'),('hour','Por hora'),('milestone','Por hito')], required=True)
    start_date       = fields.Date(default=fields.Date.context_today, required=True)
    end_date         = fields.Date()
    amount           = fields.Monetary(currency_field='company_currency', required=True)

    def action_create_contract(self):
        self.env['subcontractor_management.contract'].create({
            'subcontractor_id': self.subcontractor_id.id,
            'project_id': self.project_id.id,
            'type': self.contract_type,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'amount': self.amount,
        })
        return {'type': 'ir.actions.act_window_close'}
```

```xml
<!-- views/contract_wizard_views.xml -->
<odoo>
  <record id="view_contract_wizard" model="ir.ui.view">
    <field name="name">contract.wizard.form</field>
    <field name="model">subcontractor_management.contract_wizard</field>
    <field name="arch" type="xml">
      <form string="Nuevo Contrato" class="o_form_wizard">
        <sheet>
          <group>
            <field name="subcontractor_id"/>
            <field name="project_id"/>
            <field name="contract_type"/>
            <field name="start_date"/>
            <field name="end_date"/>
            <field name="amount"/>
          </group>
          <footer>
            <button string="Crear" type="object" name="action_create_contract" class="btn-primary"/>
            <button string="Cancelar" special="cancel" class="btn-secondary"/>
          </footer>
        </sheet>
      </form>
    </field>
  </record>
  <record id="action_contract_wizard" model="ir.actions.act_window">
    <field name="name">Nuevo Contrato</field>
    <field name="res_model">subcontractor_management.contract_wizard</field>
    <field name="view_mode">form</field>
    <field name="target">new</field>
  </record>
  <menuitem id="menu_contract_wizard" name="Nuevo Contrato"
            parent="subcontractor_management.menu_root" action="action_contract_wizard" sequence="10"/>
</odoo>
```

## 3. Dashboard de Subcontratistas

```xml
<odoo>
  <template id="dashboard_subcontractor">
    <t t-call="ofitec_theme.layout">
      <div class="row">
        <div class="col-4">
          <Card>
            <CardHeader>Contratos Activos</CardHeader>
            <CardContent>
              <Field name="subcontractor_management.contract" context="{'group_by':'subcontractor_id'}"/>
            </CardContent>
          </Card>
        </div>
        <div class="col-4">
          <Card>
            <CardHeader>Pagos Pendientes</CardHeader>
            <CardContent>
              <ChartWrapper model="subcontractor_management.payment"
                            type="pie"
                            group_by="state"
                            measure="count"/>
            </CardContent>
          </Card>
        </div>
      </div>
    </t>
  </template>
</odoo>
```

## 4. Formulario Tabulado y Tooltips

```xml
<odoo>
  <record id="view_subcontractor_form_tabbed" model="ir.ui.view">
    <field name="name">subcontractor_management.subcontractor.form.tabbed</field>
    <field name="model">subcontractor_management.subcontractor</field>
    <field name="inherit_id" ref="subcontractor_management.view_subcontractor_form"/>
    <field name="arch" type="xml">
      <sheet>
        <notebook>
          <page string="Detalles">
            <group>
              <field name="name"/>
              <field name="specialty" tooltip="Área de especialización"/>
              <field name="contact_info" tooltip="Información de contacto"/>
            </group>
          </page>
          <page string="Contratos">
            <group>
              <field name="contract_ids" widget="one2many_list"/>
            </group>
          </page>
        </notebook>
      </sheet>
    </field>
  </record>
</odoo>
```

## 5. Toasts de Feedback

```python
# models/contract_wizard.py (ajuste)
        self._cr.commit()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Contrato creado'),
                'message': _('El contrato se ha registrado con éxito.'),
                'type': 'success',
                'sticky': False,
            }
        }
```

## 6. Mobile-First

- Añadir `class="o_mobile_friendly"` en modals y usar scroll en Kanban.

---

> **Registro de cambios:** Implementadas las mejoras UI/UX para `subcontractor_management`, documentando Kanban, Wizard de contratos, Dashboard, formularios, toasts y mobile-first en su chat de módulo.



---

## Estado de Auditoría UX/UI Completa

Todos los módulos principales (`site_management`, `project_financials`, `flow_management`, `bank_connector_openbanking`, `subcontractor_management`) cuentan ahora con:

- Documentación de auditoría UX/UI.
- Propuestas de mejoras detalladas.
- Ejemplos de código para vistas Kanban, Gantt, wizards, dashboards, formularios tabulados, y toasts.
- Indicaciones mobile-first.

Con esto, la fase de auditoría y planificación de UI/UX está completa. Los siguientes pasos son implementar estos cambios en el entorno y realizar pruebas de usuario.")}]}

