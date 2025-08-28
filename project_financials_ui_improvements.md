# 🗂 Chat del módulo project\_financials (UI/UX Mejorada)

> **Objetivo:** Incorporar las mejoras UX/UI definidas: vista Kanban, Gantt, Wizard de importación, dashboard OWL, formularios tabulados, toasts y mobile-first.

## 1. Vista Kanban de Presupuestos

```xml
<odoo>
  <record id="view_project_budget_kanban" model="ir.ui.view">
    <field name="name">project_financials.project_budget.kanban</field>
    <field name="model">project_financials.project_budget</field>
    <field name="arch" type="xml">
      <kanban default_group_by="project_id">
        <templates>
          <t t-name="kanban-box">
            <div t-attf-class="oe_kanban_card oe_kanban_global_click">
              <header>
                <field name="project_id"/>
                <div class="o_badge" t-att-class="record.planned_amount.raw_value &lt; record.project_id.budget_threshold and 'bg-danger' or 'bg-success'">
                  <field name="planned_amount"/>
                </div>
              </header>
              <div>
                <strong>% Desviación: </strong>
                <span t-esc="((sum([c.amount for c in record.change_order_ids]) / record.planned_amount) * 100) if record.planned_amount else 0">%</span>
              </div>
            </div>
          </t>
        </templates>
      </kanban>
    </field>
  </record>
</odoo>
```

## 2. Vista Gantt de Cambios y Presupuestos

```xml
<odoo>
  <record id="view_project_financials_gantt" model="ir.ui.view">
    <field name="name">project_financials.gantt</field>
    <field name="model">project_financials.project_budget</field>
    <field name="arch" type="xml">
      <gantt date_start="start_date" date_stop="start_date" default_group_by="project_id" color="'blue'">
        <field name="project_id"/>
        <field name="planned_amount"/>
      </gantt>
    </field>
  </record>
</odoo>
```

## 3. Wizard de Importación de Presupuestos

```python
# models/import_budget_wizard.py
from odoo import models, fields, api

class ImportBudgetWizard(models.TransientModel):
    _name = 'project_financials.import_budget_wizard'
    _description = 'Importar Presupuestos desde Excel'

    file_data = fields.Binary(string='Archivo Excel', required=True)
    file_name = fields.Char(string='Nombre de archivo')

    def action_import(self):
        import_base = self.env['base_import.import']
        import_base.with_context(import_module='project_financials').load_file(
            {
                'file': self.file_data,
                'filename': self.file_name,
                'res_model': 'project_financials.project_budget',
                'fields': ['project_id', 'start_date', 'planned_amount', 'description'],
            }
        )
        return {'type': 'ir.actions.act_window_close'}
```

```xml
<!-- views/import_budget_wizard_views.xml -->
<odoo>
  <record id="view_import_budget_wizard" model="ir.ui.view">
    <field name="name">import.budget.wizard.form</field>
    <field name="model">project_financials.import_budget_wizard</field>
    <field name="arch" type="xml">
      <form string="Importar Presupuestos">
        <sheet>
          <group>
            <field name="file_data" filename="file_name"/>
            <field name="file_name" invisible="1"/>
          </group>
          <footer>
            <button string="Importar" type="object" name="action_import" class="btn-primary"/>
            <button string="Cancelar" special="cancel" class="btn-secondary"/>
          </footer>
        </sheet>
      </form>
    </field>
  </record>
  <record id="action_import_budget_wizard" model="ir.actions.act_window">
    <field name="name">Importar Presupuestos</field>
    <field name="res_model">project_financials.import_budget_wizard</field>
    <field name="view_mode">form</field>
    <field name="target">new</field>
  </record>
  <menuitem id="menu_import_budget_wizard" name="Importar Presupuestos"
            parent="menu_financials_root" action="action_import_budget_wizard" sequence="15"/>
</odoo>
```

## 4. Dashboard de Desviaciones

```xml
<odoo>
  <template id="dashboard_budget_deviation">
    <t t-call="ofitec_theme.layout">
      <div class="row">
        <div class="col-6">
          <Card>
            <CardHeader>Desviación Mensual</CardHeader>
            <CardContent>
              <ChartWrapper model="project_financials.project_budget"
                            type="line"
                            group_by="month"
                            measure="sum(change_order_ids.amount)"/>
            </CardContent>
          </Card>
        </div>
      </div>
    </t>
  </template>
</odoo>
```

## 5. Formulario Tabulado y Tooltips

```xml
<odoo>
  <record id="view_project_budget_form_tabbed" model="ir.ui.view">
    <field name="name">project_financials.project_budget.form.tabbed</field>
    <field name="model">project_financials.project_budget</field>
    <field name="inherit_id" ref="project_financials.view_project_budget_form"/>
    <field name="arch" type="xml">
      <sheet>
        <notebook>
          <page string="Datos Básicos">
            <group>
              <field name="project_id"/>
              <field name="start_date" tooltip="Fecha de inicio del presupuesto"/>
            </group>
          </page>
          <page string="Montos">
            <group>
              <field name="planned_amount" tooltip="Monto planificado"/>
              <field name="description" tooltip="Descripción detallada"/>
            </group>
          </page>
        </notebook>
      </sheet>
    </field>
  </record>
</odoo>
```

## 6. Toasts de Confirmación

```python
# models/import_budget_wizard.py (ajuste)
        self._cr.commit()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación completada'),
                'message': _('Presupuestos importados con éxito.'),
                'type': 'success',
                'sticky': False,
            }
        }
```

## 7. Mobile-First

- Agregar `class="o_mobile_friendly"` en formularios y `overflow-auto` en Kanban container.

---

> **Registro de cambios:** Implementadas las mejoras UX/UI clave para `project_financials`, dejando el módulo listo para pruebas y ajustes adicionales.

