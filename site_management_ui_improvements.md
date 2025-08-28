# 🗂 Chat del módulo site\_management (UI/UX Mejorada)

> **Objetivo:** Incorporar las mejoras UX/UI definidas: vista Kanban, Wizard rápido, formulario tabulado, toasts y mobile-first.

## 1. Vista Kanban de Reportes Diarios

```xml
<odoo>
  <record id="view_daily_report_kanban" model="ir.ui.view">
    <field name="name">site_management.daily_report.kanban</field>
    <field name="model">site_management.daily_report</field>
    <field name="arch" type="xml">
      <kanban default_group_by="project_id" class="o_report_kanban">
        <templates>
          <t t-name="kanban-box">
            <div t-attf-class="oe_kanban_card oe_kanban_global_click">
              <div class="o_badge">
                <field name="date"/>
              </div>
              <strong><field name="project_id"/></strong>
              <div>
                <field name="progress"/>&nbsp;%
                <small>(<field name="amount_estimated"/>)</small>
              </div>
            </div>
          </t>
        </templates>
      </kanban>
    </field>
  </record>

  <record id="action_daily_report_kanban" model="ir.actions.act_window">
    <field name="name">Reportes Diarios Kanban</field>
    <field name="res_model">site_management.daily_report</field>
    <field name="view_mode">kanban,tree,form</field>
  </record>
</odoo>
```

## 2. Wizard de Registro Rápido de Avance

```python
# models/quick_daily_wizard.py
from odoo import models, fields, api

class QuickDailyWizard(models.TransientModel):
    _name = 'site_management.quick_daily_wizard'
    _description = 'Wizard Rápido Avance Diario'

    project_id = fields.Many2one('project.project', string='Proyecto', required=True)
    date       = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    progress   = fields.Float(string='Avance (%)', required=True)
    amount_estimated = fields.Monetary(string='Costo Estimado', currency_field='company_currency', required=True)

    def action_submit(self):
        self.env['site_management.daily_report'].create({
            'project_id': self.project_id.id,
            'date': self.date,
            'progress': self.progress,
            'amount_estimated': self.amount_estimated,
        })
        return {'type': 'ir.actions.act_window_close'}
```

```xml
<!-- views/quick_daily_wizard_views.xml -->
<odoo>
  <record id="view_quick_daily_wizard" model="ir.ui.view">
    <field name="name">quick.daily.wizard.form</field>
    <field name="model">site_management.quick_daily_wizard</field>
    <field name="arch" type="xml">
      <form string="Registro Rápido Avance" class="o_form_wizard">
        <sheet>
          <group>
            <field name="project_id"/>
            <field name="date"/>
            <field name="progress"/>
            <field name="amount_estimated"/>
          </group>
          <footer>
            <button string="Registrar" type="object" name="action_submit" class="btn-primary"/>
            <button string="Cancelar" special="cancel" class="btn-secondary"/>
          </footer>
        </sheet>
      </form>
    </field>
  </record>

  <record id="action_quick_daily_wizard" model="ir.actions.act_window">
    <field name="name">Registro Rápido Avance</field>
    <field name="res_model">site_management.quick_daily_wizard</field>
    <field name="view_mode">form</field>
    <field name="target">new</field>
  </record>

  <menuitem id="menu_quick_daily_wizard" name="Registro Rápido Avance"
            parent="menu_site_management_root" action="action_quick_daily_wizard" sequence="15"/>
</odoo>
```

## 3. Formulario Tabulado y Tooltips

```xml
<odoo>
  <record id="view_daily_report_form_tabbed" model="ir.ui.view">
    <field name="name">site_management.daily_report.form.tabbed</field>
    <field name="model">site_management.daily_report</field>
    <field name="inherit_id" ref="site_management.view_daily_report_form"/>
    <field name="arch" type="xml">
      <sheet>
        <notebook>
          <page string="Información">
            <group>
              <field name="project_id"/>
              <field name="date"/>
            </group>
          </page>
          <page string="Avance">
            <group>
              <field name="progress" tooltip="Porcentaje diario de avance"/>
              <field name="amount_estimated" tooltip="Costo estimado de la faena"/>
            </group>
          </page>
          <page string="Observaciones">
            <group>
              <field name="notes"/>
            </group>
          </page>
        </notebook>
      </sheet>
    </field>
  </record>
</odoo>
```

## 4. Toasts y Feedback

- Añadir en `quick_daily_wizard.py`:

```python
from odoo import _
from odoo.exceptions import UserError

    def action_submit(self):
        self.ensure_one()
        record = self.env['site_management.daily_report'].create({
            'project_id': self.project_id.id,
            'date': self.date,
            'progress': self.progress,
            'amount_estimated': self.amount_estimated,
        })
        # Toast de confirmación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Registrado'),
                'message': _('Avance diario registrado con éxito.'),
                'type': 'success',
                'sticky': False,
            }
        }
```

## 5. Mobile-First

- En los `<form>` agregar atributos `class="o_mobile_friendly"` y usar `div` con scroll para listas Kanban.
- Probar en Chrome DevTools simulando dispositivo móvil.

---

> **Registro de cambios:** Este documento implementa el punto 3 (UI/UX mejorada) para `site_management`, incluyendo vistas Kanban, Wizard rápido, formularios tabulados, toasts y consideraciones mobile-first.



---

> **Nota:** Las mejoras de UI/UX de cada módulo ahora están documentadas en sus respectivos chats de módulo, asegurando que la información técnica y de diseño permanezca organizada y fácil de consultar en un solo lugar.

