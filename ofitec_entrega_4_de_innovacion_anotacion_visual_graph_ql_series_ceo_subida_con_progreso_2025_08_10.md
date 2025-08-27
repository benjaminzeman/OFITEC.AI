# OFITEC – Entrega 4 de Innovación (Anotación Visual, GraphQL++, Series CEO, Subida con Progreso)

> Cuarta tanda lista: **anotación visual sobre fotos QHSE**, **GraphQL++ (mutaciones clave)**, **series históricas y gráficos en CEO Dashboard**, y **subida de adjuntos grandes con barra de progreso y reanudación**. Todo Community‑safe, integrado con `of.project`, Flujo, `ai_bridge`, Portal y PWA.

---

## 0) Módulos tocados

```
custom_addons/
├─ of_qhse_vision/        # + visor OWL con bounding boxes
├─ of_api_graphql/        # + mutaciones award/approve/cashflow/task progress
├─ of_ceo_dashboard/      # + series históricas + gráfico OWL
└─ of_pwa_sync/           # + uploader con progreso y reanudación
```

---

## 1) QHSE – Anotación visual sobre la foto (OWL)

### 1.1 Assets en `of_qhse_vision/__manifest__.py`

```python
{
  # ...
  'assets': {
    'web.assets_backend': [
      'of_qhse_vision/static/src/js/annotate.js',
      'of_qhse_vision/static/src/xml/annotate.xml',
      'of_qhse_vision/static/src/css/annotate.css',
    ]
  }
}
```

### 1.2 Botón en Respuesta QHSE → abre visor

`of_qhse_vision/views/vision_views.xml`

```xml
<odoo>
  <record id="view_of_form_response_form_inherit_vision_annot" model="ir.ui.view">
    <field name="name">of.form.response.form.vision.annot</field>
    <field name="model">of.form.response</field>
    <field name="inherit_id" ref="of_qhse_forms.view_of_form_response_form"/>
    <field name="arch" type="xml">
      <header position="inside">
        <button name="action_open_annotator" type="object" string="Ver/Anotar (Visión)" class="btn-secondary"/>
      </header>
    </field>
  </record>
</odoo>
```

### 1.3 Método object para abrir el client action

`of_qhse_vision/models/forms_extend.py`

```python
from odoo import models

class OfFormResponse(models.Model):
    _inherit = 'of.form.response'

    def action_open_annotator(self):
        self.ensure_one()
        # tomar primer adjunto de la respuesta
        att = self.env['ir.attachment'].search([
            ('res_model','=','of.form.response'),('res_id','=',self.id)], limit=1)
        return {
            'type': 'ir.actions.client',
            'tag': 'of_qhse_annotate_action',
            'params': { 'response_id': self.id, 'attachment_id': att.id if att else False, 'title': self.display_name },
        }
```

### 1.4 OWL – `static/src/js/annotate.js`

```javascript
/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, useState, onMounted } from "owl";
import { useService } from "@web/core/utils/hooks";

class Annotator extends Component {
  setup(){
    this.rpc = useService('rpc');
    this.state = useState({ imgUrl:'', boxes:[], loading:true, error:null, meta:{} });
    onMounted(this.load.bind(this));
  }
  async load(){
    try{
      const p = this.props.action?.params || {};
      this.state.meta = p;
      if (!p.attachment_id){ this.state.error = 'No hay imagen adjunta'; return; }
      // URL estándar para attachments en Odoo
      this.state.imgUrl = `/web/image/ir.attachment/${p.attachment_id}/datas`;
      // obtener detecciones guardadas para esta respuesta
      const dets = await this.rpc('/of/qhse/vision/list', { response_id: p.response_id });
      this.state.boxes = dets.map(d=>({ id:d.id, label:d.kind, score:d.score||0, x1:d.x1, y1:d.y1, x2:d.x2, y2:d.y2, severity:d.severity }));
    }catch(e){ this.state.error = e.message || 'Error al cargar'; }
    finally{ this.state.loading = false; this.draw(); }
  }
  draw(){
    const img = this.el.querySelector('img.of-ann-img');
    const overlay = this.el.querySelector('canvas.of-ann-canvas');
    if (!img || !overlay) return;
    const W = overlay.width = img.clientWidth; const H = overlay.height = img.clientHeight;
    const ctx = overlay.getContext('2d'); ctx.clearRect(0,0,W,H);
    for (const b of this.state.boxes){
      ctx.strokeStyle = b.severity==='high' ? '#e55353' : (b.severity==='med' ? '#f2a654' : '#2eb85c');
      ctx.lineWidth = 2;
      ctx.strokeRect(b.x1*W, b.y1*H, (b.x2-b.x1)*W, (b.y2-b.y1)*H);
      ctx.fillStyle = 'rgba(0,0,0,.6)';
      const label = `${b.label} ${(b.score*100).toFixed(0)}%`;
      ctx.fillRect(b.x1*W, b.y1*H-18, ctx.measureText(label).width+8, 16);
      ctx.fillStyle = '#fff'; ctx.font = '12px sans-serif'; ctx.fillText(label, b.x1*W+4, b.y1*H-6);
    }
  }
  async changeSeverity(id, sev){
    await this.rpc('/of/qhse/vision/set_severity', { id, severity: sev });
    const b = this.state.boxes.find(x=>x.id===id); if (b){ b.severity = sev; this.draw(); }
  }
}

Annotator.template = 'of_qhse_vision.Annotator';
registry.category('actions').add('of_qhse_annotate_action', Annotator);
```

### 1.5 Template – `static/src/xml/annotate.xml`

```xml
<templates xml:space="preserve">
  <t t-name="of_qhse_vision.Annotator">
    <div class="of-ann-wrap">
      <t t-if="state.loading"><div class="of-ann-msg">Cargando…</div></t>
      <t t-elif="state.error"><div class="of-ann-error"><t t-esc="state.error"/></div></t>
      <t t-else="">
        <div class="of-ann-bar">
          <div class="title"><t t-esc="state.meta.title"/></div>
          <div class="legend"><span class="dot hi"></span>Alto <span class="dot me"></span>Medio <span class="dot lo"></span>Bajo</div>
        </div>
        <div class="of-ann-stage">
          <img class="of-ann-img" t-att-src="state.imgUrl" t-on-load="draw"/>
          <canvas class="of-ann-canvas"></canvas>
        </div>
        <div class="of-ann-list">
          <table>
            <thead><tr><th>Etiqueta</th><th>Conf.</th><th>Severidad</th></tr></thead>
            <tbody>
              <t t-foreach="state.boxes" t-as="b">
                <tr>
                  <td><t t-esc="b.label"/></td>
                  <td><t t-esc="(b.score*100).toFixed(0)+'%'"/></td>
                  <td>
                    <select t-on-change="(e)=>changeSeverity(b.id, e.target.value)">
                      <option value="low" t-att-selected="b.severity==='low'">Baja</option>
                      <option value="med" t-att-selected="b.severity==='med'">Media</option>
                      <option value="high" t-att-selected="b.severity==='high'">Alta</option>
                    </select>
                  </td>
                </tr>
              </t>
            </tbody>
          </table>
        </div>
      </t>
    </div>
  </t>
</templates>
```

### 1.6 Estilos – `static/src/css/annotate.css`

```css
.of-ann-wrap{ padding:12px; }
.of-ann-bar{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.of-ann-stage{ position:relative; max-width:880px; }
.of-ann-img{ width:100%; display:block; border-radius:8px; }
.of-ann-canvas{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }
.of-ann-list{ margin-top:10px; max-width:880px; }
.dot{ width:10px; height:10px; border-radius:50%; display:inline-block; margin:0 6px; }
.dot.hi{ background:#e55353; } .dot.me{ background:#f2a654; } .dot.lo{ background:#2eb85c; }
```

### 1.7 Endpoints auxiliares

`of_qhse_vision/controllers/vision.py`

```python
class VisionCtrl(http.Controller):
    @http.route('/of/qhse/vision/list', type='json', auth='user')
    def list(self, response_id):
        dets = request.env['of.qhse.detection'].sudo().search([('response_id','=',int(response_id))])
        out = []
        for d in dets:
            # si boxes_json viene como 0..1 relativo
            boxes = (json.loads(d.boxes_json or '[]') or [{}])
            for b in boxes:
                out.append({ 'id': d.id, 'kind': d.kind, 'severity': d.severity, 'score': b.get('score',0),
                             'x1': b.get('x1',0), 'y1': b.get('y1',0), 'x2': b.get('x2',0), 'y2': b.get('y2',0) })
        return out

    @http.route('/of/qhse/vision/set_severity', type='json', auth='user')
    def set_severity(self, id, severity):
        d = request.env['of.qhse.detection'].sudo().browse(int(id))
        d.write({'severity': severity})
        return {'ok': True}
```

---

## 2) GraphQL++ – Mutaciones clave

### 2.1 Mutaciones añadidas (extracto)

`of_api_graphql/controllers/graphql.py`

```python
if graphene:
    class Mutation(graphene.ObjectType):
        awardRFQ = graphene.Field(graphene.Int, rfq_id=graphene.Int(required=True), vendor_id=graphene.Int(required=True))
        approveExpense = graphene.Field(graphene.Boolean, expense_id=graphene.Int(required=True))
        registerCashflow = graphene.Field(graphene.Int, project_id=graphene.Int(), amount=graphene.Float(), status=graphene.String())
        setTaskProgress = graphene.Field(graphene.Boolean, task_id=graphene.Int(), progress=graphene.Float())

        def resolve_awardRFQ(parent, info, rfq_id, vendor_id):
            env = request.env
            rfq = env['of.rfq'].sudo().browse(rfq_id)
            bid = env['of.bid'].sudo().search([('rfq_id','=',rfq_id),('vendor_id','=',vendor_id)], limit=1)
            aw = env['of.award'].sudo().create({'rfq_id': rfq.id, 'bid_id': bid.id})
            return aw.id

        def resolve_approveExpense(parent, info, expense_id):
            e = request.env['of.gasto'].sudo().browse(expense_id)
            e.action_approve()
            return True

        def resolve_registerCashflow(parent, info, project_id, amount, status='actual'):
            cf = request.env['of.cashflow.line'].sudo().create({
                'project_id': project_id, 'amount': amount, 'status': status, 'date': request.env['ir.date'].today()})
            return cf.id

        def resolve_setTaskProgress(parent, info, task_id, progress):
            t = request.env['of.plan.task'].sudo().browse(task_id)
            t.write({'progress': progress})
            return True
```

### 2.2 Seguridad

- Estas mutaciones requieren permisos del mismo modelo subyacente.
- Para exposición externa, añade validación de **API keys** o **IP allowlist** en el controlador.

---

## 3) CEO Dashboard – Series históricas + gráfico OWL

### 3.1 Endpoint series

`of_ceo_dashboard/controllers/kpi.py`

```python
class CeoKpiApi(http.Controller):
    @http.route('/of/ceo/kpi_series', type='json', auth='user')
    def kpi_series(self, days=90):
        recs = request.env['of.ceo.kpi'].sudo().search([], order='date asc')
        recs = [r for r in recs if (request.env['ir.date'].today() - r.date).days <= int(days)]
        return [{ 'date': str(r.date), 'cash_days': r.cash_days, 'budget_dev': r.budget_deviation_pct,
                  'rfq_cycle': r.rfq_cycle_days, 'approvals_lt': r.approvals_lead_time } for r in recs]
```

### 3.2 OWL – `static/src/js/ceo.js` (extensión)

```javascript
/** @odoo-module */
import { registry } from "@web/core/registry"; import { Component, useState, onMounted } from "owl"; import { useService } from "@web/core/utils/hooks";
class CeoDash extends Component{
  setup(){ this.rpc=useService('rpc'); this.state=useState({kpis:[], series:[]}); onMounted(async()=>{ this.state.kpis = await this.rpc('/of/ceo/kpi',{}); this.state.series = await this.rpc('/of/ceo/kpi_series',{days:180}); this.draw(); }); }
  draw(){ const canvas = this.el.querySelector('canvas.ofceo-chart'); if(!canvas) return; const ctx=canvas.getContext('2d'); const W=canvas.width=canvas.clientWidth; const H=canvas.height=220; ctx.clearRect(0,0,W,H);
    const xs = this.state.series.map((p,i)=>i); const ys = this.state.series.map(p=>p.cash_days||0);
    if(!ys.length) return; const minY=Math.min(...ys,0), maxY=Math.max(...ys,1);
    const x2=(i)=> 40 + (i/(xs.length-1||1))*(W-60); const y2=(v)=> H-30 - ((v-minY)/(maxY-minY||1))*(H-60);
    // ejes
    ctx.strokeStyle='#ddd'; ctx.beginPath(); ctx.moveTo(40,10); ctx.lineTo(40,H-30); ctx.lineTo(W-20,H-30); ctx.stroke();
    // línea
    ctx.strokeStyle='#273270'; ctx.lineWidth=2; ctx.beginPath(); ys.forEach((v,i)=>{ const x=x2(i), y=y2(v); i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke();
  }
}
CeoDash.template='of_ceo_dashboard.CEO';
registry.category('actions').add('of_ceo_dashboard_action', CeoDash);
```

### 3.3 Template – `static/src/xml/ceo.xml` (extensión)

```xml
<t t-name="of_ceo_dashboard.CEO">
  <div class="ofceo">
    <div class="kpis"> ... (igual que antes) ... </div>
    <div class="chart-wrap">
      <h3>Evolución Días de Caja (180d)</h3>
      <canvas class="ofceo-chart"></canvas>
    </div>
  </div>
</t>
```

---

## 4) Subida con progreso y reanudación (adjuntos grandes)

### 4.1 Cliente: uploader con XHR y eventos de progreso

`of_pwa_sync/static/src/js/uploader.js`

```javascript
/** @odoo-module */
export async function uploadInChunks({ file, model, res_id, chunkSize=2*1024*1024, onProgress=()=>{} }){
  // init
  const init = await (await fetch('/of/pwa/upload/init', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ filename:file.name, mimetype:file.type, model, res_id }) })).json();
  const token = init.token; const total = Math.ceil(file.size/chunkSize);
  for (let i=0;i<total;i++){
    const start = i*chunkSize; const end = Math.min(file.size, start+chunkSize);
    const blob = file.slice(start,end);
    await new Promise((resolve, reject)=>{
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `/of/pwa/upload/chunk?token=${encodeURIComponent(token)}&idx=${i}`);
      xhr.upload.onprogress = (e)=>{ if (e.lengthComputable) onProgress(((i*chunkSize)+e.loaded)/file.size); };
      xhr.onload = ()=> xhr.status>=200 && xhr.status<300 ? resolve() : reject(xhr.statusText);
      xhr.onerror = ()=> reject('network'); xhr.send(blob);
    });
  }
  const fin = await (await fetch('/of/pwa/upload/finish', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ token, filename:file.name, model, res_id, mimetype:file.type }) })).json();
  onProgress(1);
  return fin.attachment_id;
}
```

### 4.2 UI de progreso (ejemplo en QHSE)

`of_qhse_forms/static/src/js/upload_widget.js`

```javascript
/** @odoo-module */
import { uploadInChunks } from "of_pwa_sync/static/src/js/uploader";
export async function uploadWithBar(file, model, res_id, barEl){
  return await uploadInChunks({ file, model, res_id, onProgress:(p)=>{ barEl.style.width = (p*100).toFixed(1)+'%'; } });
}
```

### 4.3 Backend: mejora de `finish` para ensamblar y asignar `datas`

`of_pwa_sync/controllers/upload.py`

```python
import base64, os
class ChunkUpload(http.Controller):
    # ... init/chunk como antes ...
    @http.route('/of/pwa/upload/finish', type='json', auth='user', csrf=False)
    def finish(self, token, filename, model, res_id, mimetype):
        store = request.env['ir.attachment']._filestore()
        buf = bytearray(); idx = 0
        while True:
            p = f'{store}/{token}_{idx}'
            if not os.path.exists(p): break
            with open(p, 'rb') as f: buf.extend(f.read())
            os.remove(p)
            idx += 1
        att = request.env['ir.attachment'].sudo().search([('checksum','=',token)], limit=1)
        if not att:
            att = request.env['ir.attachment'].sudo().create({'name': filename, 'res_model': model, 'res_id': int(res_id or 0), 'mimetype': mimetype})
        att.write({ 'datas': base64.b64encode(bytes(buf)) })
        return { 'ok': True, 'attachment_id': att.id }
```

### 4.4 Reanudación

- Si la subida se interrumpe, re‑llamar a `init` con el mismo archivo/model/res\_id devolverá el **mismo token** (puedes persistirlo en `localStorage`), luego seguir subiendo chunks desde el índice faltante.
- (Opcional) añadir endpoint `/of/pwa/upload/status?token=...` para listar el último `idx` recibido.

---

## 5) QA mínima

- **Anotador QHSE**: abrir respuesta con foto → ver cajas; cambiar severidad y confirmar persistencia.
- **GraphQL++**: ejecutar `awardRFQ`, `approveExpense`, `registerCashflow`, `setTaskProgress` con permisos.
- **CEO Series**: ver gráfica de Días de Caja en 180 días; snapshot diario sigue funcionando.
- **Uploader**: subir archivo de >10MB, ver barra de progreso, interrumpir y reanudar.

---

## 6) Notas

- Sin dependencias Enterprise; OWL + canvas nativo.
- Seguridad: validar grupos en mutaciones si se expone fuera; considerar API Keys.
- Escalabilidad adjuntos: para producción, mover a S3/GCS vía módulo de almacenamiento externo.
- Todas las rutas usan `of.project` como SSOT cuando aplica y mantienen auditoría con `mail.thread` (opcional).

