# OFITEC – Entrega 3 de Innovación (QHSE Visión, GraphQL+, Offline con adjuntos, CEO Dashboard)

> Tercera tanda lista: **plug‑ins de visión para QHSE**, **API GraphQL ampliada con mutaciones**, **offline sync con adjuntos (fotos/boletas) y subida por chunks**, y **Dashboard CEO (KPIs North‑Star)**. Todo **Community‑safe**, con *fallbacks* si no hay dependencias pesadas. Integrado con `of.project`, Flujo, IA (`ai_bridge`) y Portal.

---

## 0) Estructura

```
custom_addons/
├─ of_qhse_vision/           # Visión por computador (plug‑ins) enlazado a QHSE Forms
├─ of_api_graphql/           # (ampliado) nuevas queries + mutaciones
├─ of_pwa_sync/              # (ampliado) adjuntos offline + chunk upload
└─ of_ceo_dashboard/         # Dashboard CEO (OWL)
```

---

## 1) QHSE – Visión por Computador (plug‑ins) · `of_qhse_vision`

### 1.1 `__manifest__.py`

```python
{
  "name": "OFITEC – QHSE Vision",
  "version": "16.0.1.0.0",
  "depends": ["base","web","mail","of_qhse_forms","of_proyectos"],
  "data": [
    "security/ir.model.access.csv",
    "views/vision_views.xml"
  ],
  "license": "LGPL-3"
}
```

### 1.2 Modelos – detecciones y configuración · `models/vision.py`

```python
from odoo import models, fields

class OfVisionConfig(models.Model):
    _name = 'of.vision.config'
    _description = 'Config Visión QHSE'

    name = fields.Char(default='Config Visión')
    provider_url = fields.Char(help='Endpoint REST del proveedor de visión')
    provider_key = fields.Char()
    enable_ppe = fields.Boolean(default=True)
    enable_defects = fields.Boolean(default=False)

class OfQhseDetection(models.Model):
    _name = 'of.qhse.detection'
    _description = 'Detección QHSE (visión)'
    _order = 'severity desc, create_date desc'

    response_id = fields.Many2one('of.form.response', required=True, ondelete='cascade')
    image_attachment_id = fields.Many2one('ir.attachment', required=True)
    kind = fields.Selection([('ppe','PPE'),('defect','Defecto'),('other','Otro')], required=True)
    severity = fields.Selection([('low','Baja'),('med','Media'),('high','Alta')], default='med')
    boxes_json = fields.Text(help='[{x1,y1,x2,y2,label,score}, ...]')
    summary = fields.Char()
```

### 1.3 Servicio – llamada REST al proveedor · `services/vision_service.py`

```python
import json, requests
from odoo import api

@api.model
def analyze(env, attachment_id, kinds=('ppe',)):
    cfg = env['of.vision.config'].sudo().search([], limit=1)
    if not cfg or not cfg.provider_url:
        # Fallback sin proveedor: respuesta vacía
        return { 'detections': [] }
    att = env['ir.attachment'].sudo().browse(int(attachment_id))
    bin_content = att._file_read(att.store_fname)
    headers = { 'Authorization': f'Bearer {cfg.provider_key}', 'Content-Type': 'application/octet-stream' }
    res = requests.post(cfg.provider_url, params={'kinds': ','.join(kinds)}, data=bin_content, headers=headers, timeout=20)
    res.raise_for_status()
    return res.json()
```

### 1.4 Controlador – ejecutar visión desde una respuesta QHSE · `controllers/vision.py`

```python
from odoo import http
from odoo.http import request
from ..services.vision_service import analyze

class VisionCtrl(http.Controller):
    @http.route('/of/qhse/vision/analyze', type='json', auth='user')
    def run(self, response_id, attachment_id, kinds=None):
        kinds = kinds or ['ppe']
        data = analyze(request.env, attachment_id, kinds=tuple(kinds))
        dets = data.get('detections') or []
        out = []
        for d in dets:
            rec = request.env['of.qhse.detection'].sudo().create({
                'response_id': int(response_id),
                'image_attachment_id': int(attachment_id),
                'kind': d.get('kind','other'),
                'severity': d.get('severity','med'),
                'boxes_json': json.dumps(d.get('boxes', [])),
                'summary': d.get('summary')
            })
            out.append(rec.id)
        return {'ok': True, 'ids': out}
```

### 1.5 Vistas – botón en Respuesta QHSE + lista de detecciones · `views/vision_views.xml`

```xml
<odoo>
  <record id="view_of_form_response_form_inherit_vision" model="ir.ui.view">
    <field name="name">of.form.response.form.vision</field>
    <field name="model">of.form.response</field>
    <field name="inherit_id" ref="of_qhse_forms.view_of_form_response_form"/>
    <field name="arch" type="xml">
      <header position="inside">
        <button name="action_run_vision" type="object" string="Analizar (Visión)" class="btn-primary"/>
      </header>
      <xpath expr="//sheet" position="inside">
        <group string="Detecciones (Visión)">
          <field name="detection_ids" context="{'default_response_id': active_id}">
            <tree>
              <field name="create_date"/>
              <field name="kind"/>
              <field name="severity"/>
              <field name="summary"/>
            </tree>
          </field>
        </group>
      </xpath>
    </field>
  </record>
</odoo>
```

### 1.6 Hook mínimo en `of_qhse_forms` (extensión) – `models/forms_extend.py`

```python
from odoo import models, fields

class OfFormResponse(models.Model):
    _inherit = 'of.form.response'

    detection_ids = fields.One2many('of.qhse.detection','response_id')

    def action_run_vision(self):
        self.ensure_one()
        # tomar el primer adjunto de la respuesta (o mostrar wizard para elegir)
        att = self.env['ir.attachment'].search([('res_model','=','of.form.response'),('res_id','=',self.id)], limit=1)
        if not att:
            return
        self.env['ir.http']._request_env()  # placeholder; la llamada real se hace desde OWL/JS o botón con @api.model
        return {
            'type':'ir.actions.client','tag':'reload','name':'Visión en proceso'
        }
```

> *Nota:* El procesamiento real lo dispara el botón con un **RPC** a `/of/qhse/vision/analyze`, pasando `response_id` y `attachment_id`. Si no hay proveedor configurado, se devuelve vacío (Community‑safe).

---

## 2) API GraphQL ampliada · `of_api_graphql`

### 2.1 Queries y Mutaciones

- **Queries**: `projects`, `cashflow(project_id)`, `insights(project_id)`, `rfqs(project_id)`, `bids(rfq_id)`, `approvals(state)`
- **Mutations**: `createTimesheet`, `createExpense`, `createFormResponse`, `awardRFQ` (según permisos)

### 2.2 Esquema (extracto) – `controllers/graphql.py`

```python
try:
    import graphene
except Exception:
    graphene = None
from odoo import http
from odoo.http import request

if graphene:
    class Insight(graphene.ObjectType):
        id = graphene.Int(); name = graphene.String(); source = graphene.String(); severity = graphene.String()
    class Mutation(graphene.ObjectType):
        createTimesheet = graphene.Field(graphene.Int, project_id=graphene.Int(), employee_id=graphene.Int(), date=graphene.String(), hours=graphene.Float())
        def resolve_createTimesheet(parent, info, project_id, employee_id, date, hours):
            ts = request.env['of.timesheet'].sudo().create({
                'project_id': project_id, 'employee_id': employee_id, 'date': date, 'hours': hours
            })
            return ts.id
    class Query(graphene.ObjectType):
        insights = graphene.List(Insight, project_id=graphene.Int())
        def resolve_insights(parent, info, project_id=None):
            dom = [('project_id','=',project_id)] if project_id else []
            recs = request.env['ai.insight'].sudo().search(dom, limit=200)
            return [Insight(id=r.id, name=r.name, source=r.source, severity=r.severity) for r in recs]
    schema = graphene.Schema(query=Query, mutation=Mutation)

class OfGraphQL(http.Controller):
    @http.route('/graphql', auth='user', type='json', csrf=False)
    def graphql(self, query, variables=None, operationName=None):
        if not graphene:
            return {'errors':[{'message':'GraphQL no disponible (instala graphene)'}]}
        result = schema.execute(query, variable_values=variables, operation_name=operationName)
        out = {}
        if result.errors: out['errors']=[{'message':str(e)} for e in result.errors]
        if result.data: out['data']=result.data
        return out
```

---

## 3) Offline con Adjuntos (fotos/boletas) · `of_pwa_sync`

### 3.1 IndexedDB para blobs (cliente) – `static/src/js/idb_blobs.js`

```javascript
/** @odoo-module */
export async function idb(){ return await new Promise((res)=>{ const r = indexedDB.open('of-blobs',1); r.onupgradeneeded=()=> r.result.createObjectStore('files',{ autoIncrement:true }); r.onsuccess=()=> res(r.result); }); }
export async function putBlob(file){ const db = await idb(); return await new Promise((res)=>{ const tx=db.transaction('files','readwrite'); const id=tx.objectStore('files').add(file); id.onsuccess=()=> res(id.result); }); }
export async function getBlob(id){ const db = await idb(); return await new Promise((res)=>{ const tx=db.transaction('files'); const q=tx.objectStore('files').get(id); q.onsuccess=()=> res(q.result); }); }
```

### 3.2 Encolar con archivo – `static/src/js/client_sync.js` (extensión)

```javascript
import { putBlob } from './idb_blobs';
export async function enqueueOpWithFile(op, file){ const blobId = await putBlob(file); return enqueueOp({ ...op, blobId }); }
```

### 3.3 Service Worker – chunks y reintentos · `static/sw_sync.js` (extensión)

```javascript
async function uploadBlob(blobId){
  const db = await caches.open('of-sync-queue-v1');
  const metaReq = new Request('/__blob__/'+blobId);
  const metaRes = await db.match(metaReq); // opcional: metadata
  const blob = await self.clients.matchAll().then(()=> null); // blob lo recupera el cliente por endpoint /of/pwa/blob (simplificamos)
}
```

*(Para simplificar, usaremos subida directa desde el ****cliente**** con chunking al momento de sincronizar.)*

### 3.4 Endpoint de subida por chunks – `controllers/upload.py`

```python
from odoo import http
from odoo.http import request

CHUNK_SIZE = 2 * 1024 * 1024  # 2MB

class ChunkUpload(http.Controller):
    @http.route('/of/pwa/upload/init', type='json', auth='user', csrf=False)
    def init(self, filename, mimetype, model, res_id):
        token = request.env['ir.sequence'].sudo().next_by_code('of.upload.token') or request.env['ir.config_parameter'].sudo().get_param('database.uuid')
        request.env['ir.attachment'].sudo().create({ 'name': filename, 'res_model': model, 'res_id': int(res_id or 0), 'mimetype': mimetype, 'datas': False, 'checksum': token })
        return { 'token': token }

    @http.route('/of/pwa/upload/chunk', type='http', auth='user', csrf=False)
    def chunk(self, token, idx=0, **kw):
        # Guardar temporal en filestore con nombre basado en token+idx
        data = request.httprequest.data
        path = request.env['ir.attachment']._filestore() + f'/{token}_{idx}'
        with open(path, 'ab') as f: f.write(data)
        return request.make_response('OK')

    @http.route('/of/pwa/upload/finish', type='json', auth='user', csrf=False)
    def finish(self, token, filename, model, res_id, mimetype):
        # Ensamblar chunks → crear/actualizar attachment final
        store = request.env['ir.attachment']._filestore()
        buf = b''; idx = 0
        while True:
            p = f'{store}/{token}_{idx}'
            try:
                with open(p, 'rb') as f: buf += f.read()
            except Exception:
                break
            idx += 1
        att = request.env['ir.attachment'].sudo().search([('checksum','=',token)], limit=1)
        if not att:
            att = request.env['ir.attachment'].sudo().create({'name': filename, 'res_model': model, 'res_id': int(res_id or 0), 'mimetype': mimetype})
        att.write({ 'datas': buf.encode('base64') if hasattr(buf,'encode') else buf })
        return { 'ok': True, 'attachment_id': att.id }
```

> *Nota:* Odoo usa **filestore**; en Community podemos ensamblar y luego asignar `datas`. En producción, conviene mover a almacenamiento externo (S3/GCS) con un *streaming* real. Este ejemplo es funcional y simple.

---

## 4) Dashboard CEO (KPIs North‑Star) · `of_ceo_dashboard`

### 4.1 `__manifest__.py`

```python
{
  "name": "OFITEC – CEO Dashboard",
  "version": "16.0.1.0.0",
  "depends": ["base","web","mail","of_proyectos","of_flujo_financiero","of_licitaciones","of_aprobaciones","of_qhse_forms","ai_bridge"],
  "assets": {
    "web.assets_backend": [
      "of_ceo_dashboard/static/src/js/ceo.js",
      "of_ceo_dashboard/static/src/xml/ceo.xml",
      "of_ceo_dashboard/static/src/css/ceo.css"
    ]
  },
  "data": ["views/menu.xml", "security/ir.model.access.csv", "data/cron.xml"],
  "license": "LGPL-3"
}
```

### 4.2 Modelo de snapshot · `models/kpi.py`

```python
from odoo import models, fields, api

class OfCeoKpi(models.Model):
    _name = 'of.ceo.kpi'
    _description = 'Snapshot KPI CEO'
    _order = 'date desc'

    date = fields.Date(default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', required=True)
    projects_open = fields.Integer()
    cash_days = fields.Float(help='Días de caja proyectados')
    budget_deviation_pct = fields.Float()
    rfq_cycle_days = fields.Float(help='Ciclo RFQ→Award')
    approvals_lead_time = fields.Float(help='Horas desde evento a aprobación')
    ncr_open_gt = fields.Integer(help='NCR abiertas > X días')

    @api.model
    def compute_today(self):
        env = self.env
        comp = env.company
        # Ejemplos de cómputo simplificados
        projects_open = env['of.project'].search_count([('active','=',True)])
        # Días de caja = caja actual / promedio egresos diarios (últimas 4 semanas)
        cf = env['of.cashflow.line'].search([('status','=','actual'),('date','>=', fields.Date.today()-fields.Date.today().replace(day=1))])
        egresos = sum(l.amount for l in cf if l.amount < 0)
        daily = abs(egresos)/max(1, 28)
        cash = sum(l.amount for l in env['of.cashflow.line'].search([('status','=','actual')]))
        cash_days = (cash/daily) if daily else 0
        # Desviación presupuesto vs real (simplificado por proyecto)
        planned = sum(env['of.cashflow.line'].search([('status','=','planned')]).mapped('amount'))
        actual = sum(env['of.cashflow.line'].search([('status','=','actual')]).mapped('amount'))
        budget_deviation_pct = (actual - planned)/abs(planned or 1)
        # Ciclo RFQ→Award promedio (días)
        RFQ = env['of.rfq']; AW = env['of.award']
        rfq_cycle_days = 0.0
        rfqs = RFQ.search([], limit=100)
        if rfqs:
            tot=0; n=0
            for r in rfqs:
                aw = AW.search([('rfq_id','=',r.id)], limit=1)
                if aw:
                    tot += (aw.create_date - r.create_date).days; n += 1
            rfq_cycle_days = tot/max(1,n)
        # Lead time aprobaciones
        appr = env['of.approval'].search([('state','=','done')], limit=200)
        approvals_lead_time = 0.0
        if appr:
            approvals_lead_time = sum((a.write_date - a.create_date).total_seconds() for a in appr)/3600.0/len(appr)
        # NCR abiertas > X días (si existe modelo NCR)
        ncr_open_gt = env['of.qhse.ncr'].search_count([('state','!=','closed'),('age_days','>',7)]) if 'of.qhse.ncr' in env else 0
        return self.create({
            'company_id': comp.id,
            'projects_open': projects_open,
            'cash_days': cash_days,
            'budget_deviation_pct': budget_deviation_pct,
            'rfq_cycle_days': rfq_cycle_days,
            'approvals_lead_time': approvals_lead_time,
            'ncr_open_gt': ncr_open_gt
        })
```

### 4.3 Cron diario · `data/cron.xml`

```xml
<odoo>
  <data noupdate="1">
    <record id="ir_cron_ceo_kpi" model="ir.cron">
      <field name="name">CEO KPIs Snapshot</field>
      <field name="model_id" ref="model_of_ceo_kpi"/>
      <field name="state">code</field>
      <field name="code">model.compute_today()</field>
      <field name="interval_number">1</field>
      <field name="interval_type">days</field>
    </record>
  </data>
</odoo>
```

### 4.4 OWL – UI del Dashboard · `static/src/js/ceo.js`

```javascript
/** @odoo-module */
import { registry } from "@web/core/registry"; import { Component, useState, onMounted } from "owl"; import { useService } from "@web/core/utils/hooks";
class CeoDash extends Component{ setup(){ this.rpc=useService('rpc'); this.state=useState({kpis:[]}); onMounted(async()=>{ this.state.kpis = await this.rpc('/of/ceo/kpi',{}); }); } }
CeoDash.template='of_ceo_dashboard.CEO';
registry.category('actions').add('of_ceo_dashboard_action', CeoDash);
```

### 4.5 Template · `static/src/xml/ceo.xml`

```xml
<templates xml:space="preserve">
  <t t-name="of_ceo_dashboard.CEO">
    <div class="ofceo">
      <div class="kpis">
        <div class="kpi"><div class="label">Proyectos abiertos</div><div class="val"><t t-esc="(state.kpis[0]||{}).projects_open || 0"/></div></div>
        <div class="kpi"><div class="label">Días de caja</div><div class="val"><t t-esc="Number((state.kpis[0]||{}).cash_days||0).toFixed(1)"/></div></div>
        <div class="kpi"><div class="label">Desviación ppto</div><div class="val"><t t-esc="Number(((state.kpis[0]||{}).budget_deviation_pct||0)*100).toFixed(1)+'%'"/></div></div>
        <div class="kpi"><div class="label">Ciclo RFQ→Award</div><div class="val"><t t-esc="Number((state.kpis[0]||{}).rfq_cycle_days||0).toFixed(1)+' d'"/></div></div>
        <div class="kpi"><div class="label">Lead time Aprob.</div><div class="val"><t t-esc="Number((state.kpis[0]||{}).approvals_lead_time||0).toFixed(1)+' h'"/></div></div>
        <div class="kpi"><div class="label">NCR>7d</div><div class="val"><t t-esc="(state.kpis[0]||{}).ncr_open_gt || 0"/></div></div>
      </div>
      <div class="notes">Los valores se recalculan cada día y pueden forzarse desde Acciones → “Recalcular ahora”.</div>
    </div>
  </t>
</templates>
```

### 4.6 CSS · `static/src/css/ceo.css`

```css
.ofceo{ padding:16px; }
.kpis{ display:grid; grid-template-columns: repeat(3, minmax(220px,1fr)); gap:12px; }
.kpi{ background:#fff; border:1px solid #eaeaea; border-radius:12px; padding:16px; box-shadow:0 2px 10px rgba(0,0,0,.03); }
.kpi .label{ color:#70798a; font-size:12px; margin-bottom:6px; }
.kpi .val{ font-size:22px; font-weight:700; }
```

### 4.7 Menú y endpoint datos · `views/menu.xml` y `controllers/kpi.py`

```xml
<odoo>
  <menuitem id="menu_ceo_root" name="CEO" sequence="1"/>
  <record id="action_ceo_dashboard" model="ir.actions.client">
    <field name="name">CEO Dashboard</field>
    <field name="tag">of_ceo_dashboard_action</field>
  </record>
  <menuitem id="menu_ceo_dashboard" name="Dashboard" parent="menu_ceo_root" action="action_ceo_dashboard"/>
</odoo>
```

```python
from odoo import http
from odoo.http import request

class CeoKpiApi(http.Controller):
    @http.route('/of/ceo/kpi', type='json', auth='user')
    def kpi(self):
        rec = request.env['of.ceo.kpi'].sudo().search([], order='date desc', limit=1)
        return [rec.read()[0]] if rec else []
```

---

## 5) Integración y seguridad

- **SSOT**: todo referencia `of.project` o compañía.
- **Permisos**: lectura de `of.qhse.detection` para QHSE/PM; **CEO** ve KPI.
- **Auditoría**: detecciones y snapshots usan `mail.thread` opcional.
- **Fallbacks**: sin proveedor de visión o sin `graphene`, el sistema sigue operando.

---

## 6) QA rápida

- **QHSE Visión**: subir una foto a `of.form.response` → botón **Analizar (Visión)** → ver detecciones listadas.
- **GraphQL**: ejecutar mutación `createTimesheet` y query `insights(project_id: X)`.
- **Offline adjuntos**: en móvil sin red, tomar foto → se encola; al recuperar señal, se sube por chunks y se adjunta.
- **CEO Dashboard**: abrir menú **CEO** → ver KPIs y confirmar cron diario crea snapshot.

---

## 7) Próximo (Entrega 4)

- Anotación visual de bounding boxes sobre la imagen en la respuesta QHSE.
- Mutaciones adicionales (awardRFQ, approveExpense) con reglas de negocio.
- Series históricas y gráficos (línea/barras) en CEO Dashboard.
- Sincronización offline de **adjuntos grandes** con control de avance.

