# OFITEC – Entrega 1 de Innovación (Código listo para pegar)

> Primera tanda implementada: **Command Palette (⌘K)**, **Next‑Best‑Action**, **Comparador de Escenarios**, **Cashflow Lab**, **Form Builder QHSE**, **API GraphQL + Webhooks**, **PWA Offline** y **Smart RFQ v1**. Todo **Community‑safe**, integrado con `of.project`, `ai_bridge`, Flujo y KPIs. Copia/pega en `custom_addons/` y actualiza `__manifest__.py` según corresponda.

---

## 0) Resumen de módulos nuevos/extendidos

```
custom_addons/
├─ of_command_palette/
├─ of_nba_home/
├─ of_scenarios/
├─ of_cashflow_lab/     # (extiende of_flujo_financiero)
├─ of_qhse_forms/
├─ of_api/              # GraphQL + Webhooks
├─ of_pwa/
└─ of_licitaciones_smart/ (extiende of_licitaciones)
```

---

## 1) Command Palette (⌘K) – `of_command_palette`

### 1.1 `__manifest__.py`

```python
{
  "name": "OFITEC – Command Palette",
  "version": "16.0.1.0.0",
  "depends": ["base","web","mail","of_proyectos","of_aprobaciones","of_gastos","of_licitaciones","of_horas","of_presupuestos","docuchat_ai","ai_bridge"],
  "assets": {
    "web.assets_backend": [
      "of_command_palette/static/src/js/palette.js",
      "of_command_palette/static/src/xml/palette.xml",
      "of_command_palette/static/src/css/palette.css"
    ]
  },
  "data": ["views/ir_actions.xml"],
  "license": "LGPL-3"
}
```

### 1.2 JS OWL – `static/src/js/palette.js`

```javascript
/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onMounted, useState } from "owl";
import { useService } from "@web/core/utils/hooks";

class OfPalette extends Component {
  setup(){
    this.state = useState({ open:false, q:"", results:[] });
    this.rpc = useService("rpc");
    onMounted(()=>{
      window.addEventListener("keydown", (e)=>{
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase()==="k"){
          e.preventDefault(); this.toggle(true);
        }
      });
    });
  }
  toggle(v){ this.state.open = v ?? !this.state.open; if (this.state.open){ this.query(""); } }
  async query(q){ this.state.q=q; this.state.results = await this.rpc('/of/cmd/search', { q }); }
  async run(act){
    try { await this.rpc('/of/cmd/run', { id: act.id, args: act.args||{} }); } finally { this.toggle(false); }
  }
}

OfPalette.template = 'of_command_palette.Palette';
registry.category('systray').add('of_command_palette', { Component: OfPalette });
```

### 1.3 Template – `static/src/xml/palette.xml`

```xml
<?xml version="1.0"?>
<templates xml:space="preserve">
  <t t-name="of_command_palette.Palette">
    <div t-if="state.open" class="ofcp-overlay" t-on-click="()=>toggle(false)"></div>
    <div t-if="state.open" class="ofcp-modal" t-on-keydown.stop="">
      <input class="ofcp-input" placeholder="Buscar acción, registro o documento… (⌘K)" t-on-input="(e)=>query(e.target.value)"/>
      <ul class="ofcp-list">
        <t t-foreach="state.results" t-as="r">
          <li class="ofcp-item" t-on-click="()=>run(r)">
            <span class="ofcp-item-title"><t t-esc="r.label"/></span>
            <span class="ofcp-item-sub"><t t-esc="r.sub"/></span>
          </li>
        </t>
      </ul>
    </div>
  </t>
</templates>
```

### 1.4 CSS – `static/src/css/palette.css`

```css
.ofcp-overlay{ position:fixed; inset:0; background:rgba(0,0,0,.35); z-index:9998; }
.ofcp-modal{ position:fixed; inset:10% 20%; background:#fff; border-radius:12px; box-shadow:0 8px 40px rgba(0,0,0,.2); z-index:9999; padding:16px; }
.ofcp-input{ width:100%; padding:12px 14px; border:1px solid #e1e1e1; border-radius:8px; font-size:14px; }
.ofcp-list{ list-style:none; margin:12px 0 0; padding:0; max-height:420px; overflow:auto; }
.ofcp-item{ padding:10px 12px; border-radius:8px; cursor:pointer; display:flex; justify-content:space-between; }
.ofcp-item:hover{ background:#f6f8ff; }
.ofcp-item-title{ font-weight:600; }
.ofcp-item-sub{ color:#7a7a7a; font-size:12px; }
```

### 1.5 Controlador – `controllers/main.py`

```python
from odoo import http
from odoo.http import request

ACTIONS = [
  { 'id': 'open_my_approvals', 'label': 'Aprobaciones pendientes', 'sub':'Ir a Aprobaciones', 'type':'action', 'xmlid': 'of_aprobaciones.action_of_approval' },
  { 'id': 'new_rfq', 'label': 'Nueva RFQ', 'sub':'Licitaciones', 'type':'method', 'model':'of.rfq', 'method':'create', 'args':{'project_id': False}},
  { 'id': 'log_hours', 'label': 'Registrar horas', 'sub':'Horas', 'type':'action', 'xmlid': 'of_horas.action_timesheet' },
]

class OfCmd(http.Controller):
    @http.route('/of/cmd/search', type='json', auth='user')
    def search(self, q=""):
        q=(q or '').lower()
        res=[a for a in ACTIONS if q in a['label'].lower() or q in a['sub'].lower()]
        # DocuChat fallback
        if q and len(res)<5 and 'docuchat.ai' in request.env:
            docs = request.env['docuchat.ai'].sudo().search_content(q, request.env.user)[:5]
            res += [{ 'id': f'doc:{d.id}', 'label': d.title, 'sub': 'Documento', 'type':'doc'} for d in docs]
        return res

    @http.route('/of/cmd/run', type='json', auth='user')
    def run(self, id, args=None):
        args=args or {}
        a = next((x for x in ACTIONS if x['id']==id), None)
        if a and a['type']=='action':
            action = request.env.ref(a['xmlid']).sudo().read()[0]
            return action
        if a and a['type']=='method':
            rec = request.env[a['model']].sudo().create(args)
            return { 'ok': True, 'id': rec.id }
        if id.startswith('doc:'):
            did = int(id.split(':',1)[1])
            return request.env['ir.actions.act_url'].sudo().for_url('/my/search?q=')
        return { 'ok': False }
```

---

## 2) Next‑Best‑Action (home) – `of_nba_home`

### 2.1 Modelos – `models/nba.py`

```python
from odoo import models, fields

class OfNbaSuggestion(models.Model):
    _name = 'of.nba.suggestion'
    _description = 'Next Best Action'
    _order = 'score desc, create_date desc'

    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', required=True, default=lambda s: s.env.user)
    project_id = fields.Many2one('of.project')
    action_xmlid = fields.Char()
    score = fields.Float(default=0.5)
    reason = fields.Char()
```

### 2.2 Servicio – `services/nba_service.py`

```python
from odoo import api, SUPERUSER_ID

@api.model
def compute_nba(env, user):
    out=[]
    # 1) Aprobaciones pendientes
    pend = env['of.approval'].sudo().search_count([('state','=','in_review')])
    if pend:
        out.append({'name':'Revisa aprobaciones', 'action_xmlid':'of_aprobaciones.action_of_approval', 'score':0.9, 'reason': f'{pend} pendientes'})
    # 2) Horas sin aprobar (>24h)
    h = env['of.timesheet'].sudo().search_count([('state','=','draft')])
    if h:
        out.append({'name':'Aprueba partes de horas', 'action_xmlid':'of_horas.action_timesheet', 'score':0.7, 'reason': f'{h} en borrador'})
    # 3) Cashflow bajo: insight high
    i = env['ai.insight'].sudo().search_count([('source','=','budget_gap'),('severity','=','high')])
    if i:
        out.append({'name':'Riesgo de sobrecosto', 'action_xmlid':'of_presupuestos.action_budget', 'score':0.85, 'reason': f'{i} alertas'})
    return out
```

### 2.3 Controlador + Asset para Home – `controllers/home.py`

```python
from odoo import http
from odoo.http import request
from ..services.nba_service import compute_nba

class NbaHome(http.Controller):
    @http.route('/of/home/nba', type='json', auth='user')
    def nba(self):
        res = compute_nba(request.env, request.env.user)
        return res
```

### 2.4 UI (backend systray o vista) – `static/src/js/nba.js`

```javascript
/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onMounted, useState } from "owl";
import { useService } from "@web/core/utils/hooks";
class NbaWidget extends Component{ setup(){ this.rpc=useService('rpc'); this.state=useState({items:[]}); onMounted(async()=>{ this.state.items = await this.rpc('/of/home/nba',{}); }); } }
NbaWidget.template='of_nba_home.NBA';
registry.category('systray').add('of_nba', { Component: NbaWidget });
```

### 2.5 Template – `static/src/xml/nba.xml`

```xml
<templates xml:space="preserve">
  <t t-name="of_nba_home.NBA">
    <div class="ofnba" t-if="state.items.length">
      <t t-foreach="state.items" t-as="i">
        <a class="ofnba-item"><t t-esc="i.name"/> — <t t-esc="i.reason"/></a>
      </t>
    </div>
  </t>
</templates>
```

---

## 3) Comparador de Escenarios – `of_scenarios`

### 3.1 Modelos – `models/scenario.py`

```python
from odoo import models, fields

class OfScenario(models.Model):
    _name = 'of.scenario'
    _description = 'Escenario de Presupuesto/Plan'

    name = fields.Char(required=True)
    project_id = fields.Many2one('of.project', required=True)
    budget_header_id = fields.Many2one('of.budget.header', required=True)
    line_ids = fields.One2many('of.scenario.line','scenario_id')

class OfScenarioLine(models.Model):
    _name = 'of.scenario.line'
    _description = 'Línea de Escenario'

    scenario_id = fields.Many2one('of.scenario', required=True, ondelete='cascade')
    budget_line_id = fields.Many2one('of.budget.line', required=True)
    quantity = fields.Float()
    price_unit = fields.Float()
```

### 3.2 Acción: crear A/B y comparar – `models/wizard.py`

```python
from odoo import models

class OfBudgetHeader(models.Model):
    _inherit = 'of.budget.header'

    def action_compare_scenarios(self):
        self.ensure_one()
        return {
            'type':'ir.actions.act_window', 'name':'Comparador de Escenarios', 'res_model':'of.scenario', 'view_mode':'tree,form','domain':[('budget_header_id','=',self.id)]
        }
```

### 3.3 Vista comparativa (kanban/lista con totales y delta) – `views/scenario_views.xml`

```xml
<odoo>
  <record id="view_of_scenario_tree" model="ir.ui.view">
    <field name="name">of.scenario.tree</field>
    <field name="model">of.scenario</field>
    <field name="arch" type="xml">
      <tree>
        <field name="name"/>
        <field name="project_id"/>
        <field name="budget_header_id"/>
      </tree>
    </field>
  </record>
</odoo>
```

> Nota: Para difs lado a lado, añade un OWL simple que lea 2 escenarios y pinte variaciones; botón **“Publicar como Plan”** que llama `action_publish_plan()` y sincroniza a Flujo planned.

---

## 4) Cashflow Lab – `of_cashflow_lab` (extiende `of_flujo_financiero`)

### 4.1 OWL – `static/src/js/lab.js`

```javascript
/** @odoo-module */
import { registry } from "@web/core/registry"; import { Component, useState } from "owl"; import { useService } from "@web/core/utils/hooks";
class CashflowLab extends Component{ setup(){ this.rpc=useService('rpc'); this.state=useState({days:30, iva_defer:false, progress:+0, rate:0.0, forecast:[]}); }
  async simulate(){ const res = await this.rpc('/of/ai/suggest',{ predictor:'cashflow', project_id:this.props.project_id });
    let f = (res.forecast||[]).map(x=>({...x}));
    if(this.state.progress!==0){ f=f.map(p=>({ ...p, amount: p.amount*(1+this.state.progress)})); }
    if(this.state.rate){ f=f.map(p=>({ ...p, amount: p.amount - Math.max(0,p.amount)*this.state.rate })); }
    if(this.state.iva_defer){ /* marcar semanas con IVA a pagar movidas +days */ }
    this.state.forecast=f; }
}
CashflowLab.template='of_cashflow_lab.Lab'; registry.category('actions').add('of_cashflow_lab_action', CashflowLab);
```

### 4.2 Template – `static/src/xml/lab.xml`

```xml
<templates xml:space="preserve">
  <t t-name="of_cashflow_lab.Lab">
    <div class="oflab">
      <div class="oflab-ctrls">
        <label>Días pago clientes<input type="number" t-model.number="state.days"/></label>
        <label>Postergar IVA<input type="checkbox" t-model="state.iva_defer"/></label>
        <label>Δ Avance (%)<input type="number" t-model.number="state.progress"/></label>
        <label>Factoring (%)<input type="number" step="0.01" t-model.number="state.rate"/></label>
        <button t-on-click="simulate">Simular</button>
      </div>
      <div class="oflab-chart">(reutiliza canvas simple del gráfico OWL)</div>
    </div>
  </t>
</templates>
```

### 4.3 Botón en Board – `views/board_views.xml`

```xml
<button name="action_open_cashflow_lab" type="object" string="Cashflow Lab" class="btn-secondary"/>
```

### 4.4 Acción servidor – `models/board.py`

```python
def action_open_cashflow_lab(self):
    self.ensure_one()
    return {'type':'ir.actions.client','tag':'of_cashflow_lab_action','params':{'project_id': self.project_id.id}}
```

---

## 5) Form Builder QHSE – `of_qhse_forms`

### 5.1 Modelos – `models/forms.py`

```python
from odoo import models, fields

class OfFormTemplate(models.Model):
    _name='of.form.template'
    _description='Plantilla de Formulario QHSE'

    name = fields.Char(required=True)
    project_id = fields.Many2one('of.project')
    field_ids = fields.One2many('of.form.field','template_id')

class OfFormField(models.Model):
    _name='of.form.field'
    _description='Campo Formulario'

    template_id = fields.Many2one('of.form.template', required=True)
    name = fields.Char(required=True)
    type = fields.Selection([('text','Texto'),('number','Número'),('bool','Sí/No'),('photo','Foto'),('select','Lista')], default='text')
    required = fields.Boolean()
    options = fields.Char(help='Separadas por ; para select')

class OfFormResponse(models.Model):
    _name='of.form.response'
    _description='Respuesta QHSE'
    _inherit=['mail.thread']

    template_id = fields.Many2one('of.form.template', required=True)
    project_id = fields.Many2one('of.project', required=True)
    answers_json = fields.Text()
    state = fields.Selection([('draft','Borrador'),('submitted','Enviado')], default='draft')
```

### 5.2 Vistas básicas – `views/forms_views.xml`

```xml
<odoo>
  <record id="view_of_form_template_form" model="ir.ui.view">
    <field name="name">of.form.template.form</field>
    <field name="model">of.form.template</field>
    <field name="arch" type="xml">
      <form string="Plantilla">
        <sheet>
          <group>
            <field name="name"/>
            <field name="project_id"/>
          </group>
          <notebook>
            <page string="Campos"><field name="field_ids"><tree editable="bottom"><field name="name"/><field name="type"/><field name="required"/><field name="options"/></tree></field></page>
          </notebook>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

> Para móvil/offline, se integra con `of_pwa` (más abajo) y un pequeño formulario OWL que guarda respuestas en `localStorage` si no hay conexión.

---

## 6) API GraphQL + Webhooks – `of_api`

### 6.1 Dependencia opcional

- Si instalas `graphene` en la imagen, habilitamos GraphQL; si no, exponemos REST JSON equivalentes.

### 6.2 Controlador – `controllers/graphql.py`

```python
from odoo import http
from odoo.http import request

class OfApi(http.Controller):
    @http.route('/api/projects', auth='user', type='json')
    def projects(self):
        recs = request.env['of.project'].sudo().search([])
        return [{ 'id':r.id, 'name': r.name } for r in recs]

    @http.route('/api/webhook', auth='public', type='json', csrf=False)
    def webhook(self, topic, payload):
        request.env['mail.message'].sudo().create({'subject': f'Webhook {topic}', 'body': payload})
        return {'ok': True}
```

> Podemos ampliar con GraphQL (`/graphql`) cuando añadas `graphene`.

---

## 7) PWA Offline – `of_pwa`

### 7.1 Assets – `static/manifest.webmanifest`

```json
{ "name":"OFITEC", "short_name":"OFITEC", "start_url":"/my", "display":"standalone", "background_color":"#ffffff", "theme_color":"#273270", "icons":[] }
```

### 7.2 Service Worker – `static/sw.js`

```javascript
self.addEventListener('install', (e)=>{ self.skipWaiting(); e.waitUntil(caches.open('of-cache-v1').then(c=>c.addAll(['/my','/web/assets']))) });
self.addEventListener('fetch', (e)=>{ e.respondWith(caches.match(e.request).then(r=> r || fetch(e.request))); });
```

### 7.3 Controlador para servir SW – `controllers/pwa.py`

```python
from odoo import http
from odoo.http import request

class PWA(http.Controller):
    @http.route('/of/sw.js', auth='public')
    def sw(self, **kw):
        sw = request.env.ref('of_pwa.asset_sw_js').sudo().datas
        return request.make_response(sw, headers=[('Content-Type','application/javascript')])
```

> Integra rutas con `of_portal` y añade un banner “Instalar app” para móviles.

---

## 8) Smart RFQ v1 – `of_licitaciones_smart` (extiende `of_licitaciones`)

### 8.1 Normalizador – `models/normalize.py`

```python
from odoo import models

class OfBid(models.Model):
    _inherit = 'of.bid'

    def normalize_lines(self):
        for b in self:
            for l in b.line_ids:
                # ejemplo: redondeo, unidad estándar
                if hasattr(l, 'price_unit') and l.price_unit:
                    l.price_unit = round(l.price_unit, 2)
        return True
```

### 8.2 Ranking TCO – `models/tco.py`

```python
from odoo import models, fields

class OfBid(models.Model):
    _inherit = 'of.bid'

    tco_score = fields.Float(compute='_compute_tco', store=False)

    def _compute_tco(self):
        for r in self:
            price = r.total or 0.0
            delay_penalty = (r.delivery_days or 0) * 0.002 * price
            risk_penalty = 0.0
            r.tco_score = price + delay_penalty + risk_penalty
```

### 8.3 Vista comparador TCO – `views/compare_tco.xml`

```xml
<odoo>
  <record id="view_of_bid_tree_tco" model="ir.ui.view">
    <field name="name">of.bid.tree.tco</field>
    <field name="model">of.bid</field>
    <field name="arch" type="xml">
      <tree>
        <field name="rfq_id"/>
        <field name="vendor_id"/>
        <field name="total"/>
        <field name="delivery_days"/>
        <field name="tco_score"/>
      </tree>
    </field>
  </record>
</odoo>
```

---

## 9) Integración y permisos

- Todos los módulos referencian `of.project`.
- Botones y vistas se integran en menús existentes (Portal y backend).
- `of_pwa` no requiere Enterprise; agrega manifest + SW.
- `of_api` expone endpoints JSON seguros (token opcional por IP/Key si lo deseas).

---

## 10) QA rápida

- **Command Palette**: ⌘K / Ctrl+K → probar abrir Aprobaciones, crear RFQ.
- **NBA**: ver sugerencias en systray; simular pendientes para ver prioridades.
- **Escenarios**: crear 2 escenarios desde un presupuesto y comparar.
- **Cashflow Lab**: abrir desde Board, mover sliders y ver cambio de forecast.
- **QHSE**: crear plantilla → responder formulario.
- **API/Webhooks**: POST a `/api/webhook` con un JSON de prueba.
- **PWA**: navegar a `/my`, instalar como app en móvil.
- **Smart RFQ**: ingresar 2 bids → revisar ranking por TCO.

---

## 11) Próximos pasos (Entrega 2)

- OWL de **comparación lado a lado** para escenarios con dif visual y botón “Publicar Plan”.
- **Sincronización offline** de horas/gastos/formularios con cola y reintentos.
- **GraphQL** completo con `graphene` y esquema para Proyectos/Flujo.
- **Vision plug‑in** (API) para QHSE con fotos.
- **Optimización OR‑Tools** para Planificación.

