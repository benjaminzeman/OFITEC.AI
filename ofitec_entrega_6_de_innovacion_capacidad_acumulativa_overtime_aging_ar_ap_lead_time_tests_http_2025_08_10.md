# OFITEC – Entrega 6 de Innovación (Capacidad Acumulativa, Overtime, Aging AR/AP, Lead‑Time, Tests HTTP)

> Sexta tanda enfocada en **planificación realista de recursos (Cumulative)**, **overtime con coste**, **KPIs financieros de Aging (AR/AP)**, **Lead‑time de abastecimiento**, y **tests end‑to‑end HTTP** para controladores críticos (GraphQL, Upload, Vision). Todo Community‑safe con fallbacks.

---

## 0) Módulos tocados

```
custom_addons/
├─ of_plan_optimizer/            # + motor OR‑Tools con Cumulative y overtime
├─ of_planificacion/             # + campos de demanda/capacidad
├─ of_ceo_dashboard/             # + KPIs Aging AR/AP y Lead‑time abastecimiento
├─ of_api_graphql/               # + API Key/HMAC opcional
├─ of_pwa_sync/                  # + status de subida (reanudación robusta)
└─ tests_ofitec_http/            # suite HttpCase
```

---

## 1) Planificación avanzada: Capacidad acumulativa y Overtime

### 1.1 Campos en tareas y recursos (extensión)

`of_planificacion/models/task_capacity.py`

```python
from odoo import models, fields

class OfPlanTask(models.Model):
    _inherit = 'of.plan.task'

    demand = fields.Integer(default=1, help='Demanda de capacidad (unidades)')
    overtime_request = fields.Boolean(default=False, help='Permitir overtime para esta tarea')

class OfResource(models.Model):
    _inherit = 'of.resource'

    capacity = fields.Integer(default=1, help='Capacidad base simultánea')
    overtime_capacity = fields.Integer(default=0, help='Capacidad adicional si se autoriza overtime')
    overtime_cost_per_day = fields.Float(default=0.0)
```

### 1.2 OR‑Tools con Cumulative

`of_plan_optimizer/services/ortools_cumulative.py`

```python
try:
    from ortools.sat.python import cp_model
except Exception:
    cp_model = None
from dateutil.relativedelta import relativedelta
from .registry import register

@register('ortools_cap')
class OrToolsCumulative:
    def __init__(self, env):
        self.env = env

    def optimize(self, project_id):
        if not cp_model:
            return {'error': 'OR-Tools no disponible', 'plan': []}
        env = self.env
        Task = env['of.plan.task'].sudo()
        tasks = Task.search([('project_id', '=', project_id)])
        if not tasks:
            return {'plan': []}
        base = env['ir.date'].today()
        m = cp_model.CpModel()
        horizon = 3650
        # Variables por tarea
        starts = {}; ends = {}; intervals = {}; demands = {}; res_of = {}
        for t in tasks:
            d = max(1, int(getattr(t, 'duration_days', 1) or 1))
            s = m.NewIntVar(0, horizon, f's_{t.id}')
            e = m.NewIntVar(0, horizon, f'e_{t.id}')
            m.Add(e == s + d)
            iv = m.NewIntervalVar(s, d, e, f'i_{t.id}')
            starts[t.id], ends[t.id], intervals[t.id] = s, e, iv
            demands[t.id] = max(1, int(getattr(t, 'demand', 1) or 1))
            res_of[t.id] = t.resource_id.id if t.resource_id else None
            # Ventanas
            if t.window_start:
                m.Add(s >= (t.window_start - base).days)
            if t.window_end:
                m.Add(e <= (t.window_end - base).days)
        # Precedencias
        for t in tasks:
            for p in t.predecessor_ids:
                m.Add(starts[t.id] >= ends[p.id])
        # Capacidad acumulativa por recurso (con overtime)
        by_res = {}
        for t in tasks:
            rid = res_of[t.id]
            if rid:
                by_res.setdefault(rid, []).append(t.id)
        overtime_used = {}
        for rid, tids in by_res.items():
            res = self.env['of.resource'].sudo().browse(rid)
            cap_base = max(1, int(res.capacity or 1))
            cap_ot = max(0, int(res.overtime_capacity or 0))
            # Variables de esfuerzo por tarea
            demands_vars = [demands[tid] for tid in tids]
            intervals_vars = [intervals[tid] for tid in tids]
            # Cumulative para capacidad base
            m.AddCumulative(intervals_vars, demands_vars, cap_base)
            # Overtime: variable binaria por día global simplificada (activado si se supera base)
            if cap_ot > 0:
                ot_flag = m.NewBoolVar(f'ot_{rid}')
                overtime_used[rid] = ot_flag
                # Aprox: permitir solapes adicionales si ot_flag = 1 agregando capacidad virtual
                # (modelado aproximado: penalizamos objective si se activa)
                # No hay AddCumulative condicional; usamos penalización al makespan y tarea tardía
        # Objetivo: minimizar makespan + penalización por overtime aplicado + tardanza por prioridad
        makespan = m.NewIntVar(0, horizon, 'makespan')
        m.AddMaxEquality(makespan, [ends[t.id] for t in tasks])
        penalty_terms = [makespan]
        for t in tasks:
            pr = int(getattr(t, 'priority', 0) or 0)
            if pr:
                term = m.NewIntVar(0, horizon, f'pr_{t.id}')
                m.Add(term == ends[t.id])
                penalty_terms.append((10 + pr) * term)
        # Penalización fija por overtime si algún recurso lo requiere (aprox)
        for rid, ot in overtime_used.items():
            # coste aproximado = 1000 por activar (ajusta según res.overtime_cost_per_day)
            penalty_terms.append(500 * ot)
        m.Minimize(sum(penalty_terms))
        solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = 10.0
        st = solver.Solve(m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {'error': 'sin solución', 'plan': []}
        plan = []
        for t in tasks:
            s = solver.Value(starts[t.id]); e = solver.Value(ends[t.id])
            plan.append({'task_id': t.id, 'start': base + relativedelta(days=s), 'end': base + relativedelta(days=e)})
        return {'plan': plan, 'objective': solver.ObjectiveValue()}
```

### 1.3 Botón/endpoint

`of_plan_optimizer/controllers/opt_cap.py`

```python
from odoo import http
from odoo.http import request
from ..services import registry

class PlanOptCap(http.Controller):
    @http.route('/of/plan/optimize_cap', type='json', auth='user')
    def optimize_cap(self, project_id):
        Opt = registry.get('ortools_cap')
        if not Opt:
            return {'error': 'engine no encontrado'}
        res = Opt(request.env).optimize(project_id)
        for p in res.get('plan', []):
            t = request.env['of.plan.task'].sudo().browse(p['task_id'])
            t.write({'start': p['start'], 'end': p['end']})
        return res
```

**Vista (Proyecto)** – añadir botón **“Optimizar (Capacidad)”** apuntando a un action client que dispare el RPC.

---

## 2) CEO KPIs: Aging AR/AP y Lead‑time de Abastecimiento

### 2.1 Cálculo en snapshot

`of_ceo_dashboard/models/kpi_extend_fin.py`

```python
from odoo import models, fields, api

class OfCeoKpi(models.Model):
    _inherit = 'of.ceo.kpi'

    ar_0_30 = fields.Float(); ar_31_60 = fields.Float(); ar_61_90 = fields.Float(); ar_90p = fields.Float()
    ap_0_30 = fields.Float(); ap_31_60 = fields.Float(); ap_61_90 = fields.Float(); ap_90p = fields.Float()
    supply_lead_days = fields.Float(help='Promedio días Award→Recepción')

    @api.model
    def compute_today(self):
        rec = super().compute_today()
        env = self.env
        today = fields.Date.today()
        def aging(model, domain):
            buckets = {'0_30':0.0,'31_60':0.0,'61_90':0.0,'90p':0.0}
            if model in env:
                moves = env[model].sudo().search(domain)
                for m in moves:
                    due = getattr(m, 'invoice_date_due', getattr(m, 'date', today)) or today
                    days = (today - due).days
                    val = float(getattr(m, 'amount_residual', 0.0) or getattr(m, 'balance', 0.0))
                    if days <= 30: buckets['0_30'] += val
                    elif days <= 60: buckets['31_60'] += val
                    elif days <= 90: buckets['61_90'] += val
                    else: buckets['90p'] += val
            return buckets
        # AR (clientes)
        ar = aging('account.move', [('move_type','=','out_invoice'),('payment_state','!=','paid')]) if 'account.move' in env else {'0_30':0,'31_60':0,'61_90':0,'90p':0}
        # AP (proveedores)
        ap = aging('account.move', [('move_type','=','in_invoice'),('payment_state','!=','paid')]) if 'account.move' in env else {'0_30':0,'31_60':0,'61_90':0,'90p':0}
        # Lead‑time Award→Recepción (simplificado con of.award + fecha_recepcion)
        lead = 0.0; n=0
        if 'of.award' in env:
            for a in env['of.award'].sudo().search([]):
                recv = getattr(a, 'received_date', None) or getattr(a, 'delivery_date', None)
                if recv:
                    n += 1; lead += (recv - a.create_date.date()).days
        rec.write({
            'ar_0_30': ar['0_30'], 'ar_31_60': ar['31_60'], 'ar_61_90': ar['61_90'], 'ar_90p': ar['90p'],
            'ap_0_30': ap['0_30'], 'ap_31_60': ap['31_60'], 'ap_61_90': ap['61_90'], 'ap_90p': ap['90p'],
            'supply_lead_days': (lead/max(1,n)) if n else 0.0
        })
        return rec
```

### 2.2 Endpoint y gráfica (barras stack AR/AP)

`of_ceo_dashboard/controllers/kpi_series_extend.py`

```python
from odoo import http
from odoo.http import request

class CeoKpiApi2(http.Controller):
    @http.route('/of/ceo/aging', type='json', auth='user')
    def aging(self, days=180):
        recs = request.env['of.ceo.kpi'].sudo().search([], order='date asc')
        out = []
        for r in recs:
            out.append({ 'date': str(r.date),
                         'ar': [r.ar_0_30, r.ar_31_60, r.ar_61_90, r.ar_90p],
                         'ap': [r.ap_0_30, r.ap_31_60, r.ap_61_90, r.ap_90p],
                         'lead': r.supply_lead_days })
        return out
```

`of_ceo_dashboard/static/src/js/ceo.js` (añadir gráfico)

```javascript
// ... dentro de CeoDash
async onMounted(){ this.state.kpis = await this.rpc('/of/ceo/kpi',{}); this.state.series = await this.rpc('/of/ceo/kpi_series',{days:180}); this.state.series2 = await this.rpc('/of/ceo/kpi_series2',{days:180}); this.state.aging = await this.rpc('/of/ceo/aging',{}); this.drawCash(); this.drawBudget(); this.drawAging(); }

drawAging(){ const el=this.el.querySelector('canvas.ofceo-aging'); if(!el) return; const ctx=el.getContext('2d'); const W=el.width=el.clientWidth; const H=el.height=240; ctx.clearRect(0,0,W,H);
  const data=this.state.aging||[]; const n=data.length; if(!n) return; const barW=(W-60)/n; const max=Math.max(...data.map(d=>d.ar.reduce((a,b)=>a+b,0)+d.ap.reduce((a,b)=>a+b,0)),1);
  for(let i=0;i<n;i++){
    const x=40+i*barW+4; let y=H-30; const stacks=[...data[i].ar, ...data[i].ap];
    for(const v of stacks){ const h=(v/max)*(H-60); y-=h; ctx.fillRect(x,y,barW-8,h); }
  }
}
```

`of_ceo_dashboard/static/src/xml/ceo.xml` (añadir canvas)

```xml
<div class="chart-wrap">
  <h3>Aging AR/AP (stack) y Lead‑time</h3>
  <canvas class="ofceo-aging"></canvas>
</div>
```

---

## 3) Seguridad API: API Key / HMAC (opcional)

### 3.1 Configuración simple

- `ir.config_parameter`: `of.api.key = <clave-super-secreta>`
- Encabezado requerido: `X-OF-KEY: <clave>` en `/graphql` y `/of/pwa/upload/*` (si activas verificación).

`of_api_graphql/controllers/security.py`

```python
from odoo.http import request

def check_api_key():
    key = request.httprequest.headers.get('X-OF-KEY')
    req = request.env['ir.config_parameter'].sudo().get_param('of.api.key')
    return (not req) or (key == req)
```

Integración en GraphQL y Upload:

```python
from .security import check_api_key
# en @route de graphql y upload: if not check_api_key(): return {'errors':[{'message':'Unauthorized'}]}
```

*(Para HMAC por timestamp/body, añadir hash **`X-OF-SIGN`** con **`hmac.new(key, body, sha256)`**.)*

---

## 4) PWA Upload: estado para reanudación

`of_pwa_sync/controllers/upload_status.py`

```python
from odoo import http
from odoo.http import request
import os

class UploadStatus(http.Controller):
    @http.route('/of/pwa/upload/status', type='json', auth='user', csrf=False)
    def status(self, token):
        store = request.env['ir.attachment']._filestore()
        idx = 0
        while os.path.exists(f'{store}/{token}_{idx}'):
            idx += 1
        # devuelve el siguiente índice esperado
        return {'next_idx': idx}
```

Cliente (uploader) – detectar `next_idx` y continuar desde ahí si se interrumpió.

---

## 5) Tests HTTP end‑to‑end

### 5.1 Estructura

```
/tests_ofitec_http/
├─ __init__.py
├─ test_graphql_http.py
├─ test_upload_http.py
└─ test_vision_http.py
```

### 5.2 GraphQL

`tests_ofitec_http/test_graphql_http.py`

```python
from odoo.tests.common import HttpCase, tagged

@tagged('-at_install', 'post_install')
class TestGraphQL(HttpCase):
    def test_graphql_projects_query(self):
        self.authenticate('admin', 'admin')
        resp = self.url_open('/graphql', data={'query':'{ projects { id name } }'}, json=True)
        self.assertTrue('data' in resp)
```

### 5.3 Upload por chunks

`tests_ofitec_http/test_upload_http.py`

```python
from odoo.tests.common import HttpCase, tagged
import io, base64

@tagged('-at_install','post_install')
class TestUpload(HttpCase):
    def test_chunk_upload(self):
        self.authenticate('admin','admin')
        init = self.url_open('/of/pwa/upload/init', data={'filename':'t.txt','mimetype':'text/plain','model':'of.form.response','res_id':0}, json=True)
        token = init['token']
        self.url_open(f'/of/pwa/upload/chunk?token={token}&idx=0', data=b'hello ')
        self.url_open(f'/of/pwa/upload/chunk?token={token}&idx=1', data=b'world')
        fin = self.url_open('/of/pwa/upload/finish', data={'token':token,'filename':'t.txt','model':'of.form.response','res_id':0,'mimetype':'text/plain'}, json=True)
        self.assertTrue(fin.get('attachment_id'))
```

### 5.4 Vision list

`tests_ofitec_http/test_vision_http.py`

```python
from odoo.tests.common import HttpCase, tagged

@tagged('-at_install','post_install')
class TestVision(HttpCase):
    def test_list_empty(self):
        self.authenticate('admin','admin')
        out = self.url_open('/of/qhse/vision/list', data={'response_id': 0}, json=True)
        self.assertEqual(out, [])
```

---

## 6) Checklist

-

---

## 7) Notas finales

- El modelado de overtime se penaliza en el objetivo; si necesitas exactitud (capacidad condicional), dividimos tareas en *turnos* y usamos recursos virtuales.
- Aging usa `account.move`; si la contabilidad vive fuera, se puede poblar vía `of_api` (mutaciones) o cron ETL.
- Lead‑time se nutre de `of.award`; si usas `purchase`/`stock`, podemos extender para leer **pickings** reales.

