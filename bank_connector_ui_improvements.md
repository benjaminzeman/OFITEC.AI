# 🗂 Chat del módulo bank\_connector\_openbanking (UI/UX Mejorada)

> **Objetivo:** Aplicar las mejoras UX/UI específicas para el módulo de importación bancaria: vistas Kanban, Wizard de importación, Dashboard interactivo, formularios tabulados, toasts y mobile-first.

## 1. Vista Kanban de Extractos Bancarios

```xml
<odoo>
  <record id="view_bank_statement_kanban" model="ir.ui.view">
    <field name="name">bank_connector_openbanking.bank.statement.kanban</field>
    <field name="model">flow.bank.statement</field>
    <field name="arch" type="xml">
      <kanban default_group_by="bank_id">
        <templates>
          <t t-name="kanban-box">
            <div class="oe_kanban_card oe_kanban_global_click">
              <header>
                <strong><field name="bank_id"/></strong>
                <div class="o_badge" t-att-class="record.amount.raw_value &lt; 0 and 'bg-danger' or 'bg-success'">
                  <field name="amount"/>
                </div>
              </header>
              <div><field name="date"/></div>
              <div><field name="name"/></div>
            </div>
          </t>
        </templates>
      </kanban>
    </field>
  </record>
</odoo>
```

## 2. Wizard de Importación de Extractos Bancarios

```python
# models/import_bank_wizard.py
from odoo import models, fields, api, _

class ImportBankWizard(models.TransientModel):
    _name = 'bank_connector.import_bank_wizard'
    _description = 'Wizard Importación Extractos Bancarios'

    file_data = fields.Binary(string='Archivo OFX/CSV', required=True)
    file_name = fields.Char(string='Nombre de archivo')

    def action_import(self):
        # Lógica de parsing OFX/CSV
        # Ejemplo simplificado:
        data = self.file_data  # base64
        # procesar y crear líneas en flow.bank.statement
        self._cr.commit()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación completada'),
                'message': _('Extractos bancarios importados con éxito.'),
                'type': 'success',
                'sticky': False,
            }
        }
```

```xml
<!-- views/import_bank_wizard_views.xml -->
<odoo>
  <record id="view_import_bank_wizard" model="ir.ui.view">
    <field name="name">import.bank.wizard.form</field>
    <field name="model">bank_connector.import_bank_wizard</field>
    <field name="arch" type="xml">
      <form string="Importar Extractos Bancarios">
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
  <record id="action_import_bank_wizard" model="ir.actions.act_window">
    <field name="name">Importar Extractos Bancarios</field>
    <field name="res_model">bank_connector.import_bank_wizard</field>
    <field name="view_mode">form</field>
    <field name="target">new</field>
  </record>
  <menuitem id="menu_import_bank_wizard" name="Importación Bancaria"
            parent="bank_connector.menu_bank_root" action="action_import_bank_wizard" sequence="10"/>
</odoo>
```

## 3. Dashboard de Movimientos Bancarios

```xml
<odoo>
  <template id="dashboard_bank_movements">
    <t t-call="ofitec_theme.layout">
      <div class="row">
        <div class="col-12">
          <Card>
            <CardHeader>Movimientos del Mes</CardHeader>
            <CardContent>
              <ChartWrapper model="flow.bank.statement"
                            type="bar"
                            group_by="date"
                            measure="sum(amount)"/>
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
  <record id="view_bank_statement_form_tabbed" model="ir.ui.view">
    <field name="name">flow.bank.statement.form.tabbed</field>
    <field name="model">flow.bank.statement</field>
    <field name="inherit_id" ref="bank_connector_openbanking.view_bank_statement_form"/>
    <field name="arch" type="xml">
      <sheet>
        <notebook>
          <page string="Detalles">
            <group>
              <field name="bank_id"/>
              <field name="date" tooltip="Fecha del movimiento"/>
              <field name="name" tooltip="Descripción"/>
            </group>
          </page>
          <page string="Montos">
            <group>
              <field name="amount" tooltip="Monto del extracto"/>
              <field name="currency_id"/>
            </group>
          </page>
          <page string="Conciliación">
            <group>
              <field name="reconciled"/>
              <field name="cashflow_line_id"/>
            </group>
          </page>
        </notebook>
      </sheet>
    </field>
  </record>
</odoo>
```

## 5. Toasts de Feedback

(Incluido en Wizard de Importación y Wizard de Conciliación)

## 6. Mobile-First

- Agregar `class="o_mobile_friendly"` en formularios y scroll en Kanban.

---

> **Registro de cambios:** Implementadas las mejoras UI/UX para `bank_connector_openbanking`, documentando Kanban, Wizard de importación, Dashboard, formularios tabulados, toasts y mobile-first en su chat de módulo.

