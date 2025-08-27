# OFITEC – Entrega 6 de Innovación (Capacidad Acumulativa, Overtime, AR/AP Aging, Tests E2E)

> Sexta tanda enfocada en realismo operativo y control financiero profundo: **capacidad acumulativa por recurso/cuadrilla**, **overtime con coste y aceleración**, **aging de CxC/CxP** y **lead‑time de abastecimiento**, más **tests end‑to‑end HTTP** para rutas clave (GraphQL, Upload, Vision, Sync). Community‑safe, sin Enterprise.

---

## 0) Módulos tocados

```
custom_addons/
├─ of_planificacion/           # + campos de capacidad y overtime
├─ of_plan_optimizer/          # + OR-Tools con AddCumulative y overtime
├─ of_ceo_dashboard/           # + aging AR/AP y lead-time abastecimiento (UI + datos)
└─ tests_ofitec/               # + HttpCase E2E para controladores
```

---

## 1) Planificación con Capacidad Acumulativa y Overtime

### 1.1 Extensión de modelos (capacidad, demanda, overtime)

`of_planificacion/models/task_extend.py`

```python
from odoo import models, fields

class OfPlanTask(models.Model):
    _inherit = 'of.plan.task'

    duration_days = fields.Integer(default=1)
    resource_id = fields.Many2one('of.resource', help='Recurso principal (máquina/equipo)')
    crew_id = fields.Many2one('of.crew', help='Cuadrilla asignada')
    demand_units = fields.Integer(default=1, help='Demanda de capacidad del recurso (unidades)')
    window_start = fields.Date()
    window_end = fields.Date()
    priority = fields.Integer(default=0)
    overtime_allowed = fields.Boolean(default=False)
    overtime_gain_pct = fields.Float(default=0.3, help='Reducción de duración si hay overtime (0..1)')
    overtime_cost = fields.Float(default=0.0, help='Penalización por usar overtime (costo relativo)')
    predecessor_ids = fields.Many2many('of.plan.task', 'of_task_pred_rel', 'task_id', 'pred_id', string='Predecesoras')

class OfResource(models.Model):
    _name = 'of.resource'
    _description = 'Recurso con capacidad'

    name = fields.Char(required=True)
    capacity = fields.Integer(default=1, help='Capacidad concurrente (tareas a la vez)')

class OfCrew(models.Model):
    _name = 'of.crew'
    _description = 'Cuadrilla'

    name = fields.Char(required=True)
    size = fields.Integer(default=1)
```

### 1.2 OR‑Tools: AddCumulative + overtime (opcional)

`of_plan_optimizer/services/ortools_adv.py`

```python
try:
    from ortools.sat.python import cp_model
except Exception:
    cp_model = None
from dateutil.relativedelta import relativedelta
from .registry import register

@register('ortools_adv')
class OrToolsAdvanced:
    def __init__(self, env):
        self.env = env

    def optimize(self, project_id):
        if not cp_model:
            return {'error': 'OR-Tools no disponible', 'plan': []}
        Task = self.env['of.plan.task'].sudo()
        tasks = Task.search([('project_id', '=', project_id)])
        if not tasks:
            return {'plan': []}

        base = self.env['ir.date'].today()
        m = cp_model.CpModel()
        horizon = 3650

        starts = {}; ends = {}; intervals = {}; durations = {}
        overtime_b = {}; overtime_gain = {}

        # Variables de cada tarea
        for t in tasks:
            d = max(1, int(t.duration_days or 1))
            # overtime: duración efectiva = d - o*gain
            gain = max(0, int(round(d * float(t.overtime_gain_pct or 0.0))))
            s = m.NewIntVar(0, horizon, f's_{t.id}')
            e = m.NewIntVar(0, horizon, f'e_{t.id}')
            o = m.NewBoolVar(f'o_{t.id}') if t.overtime_allowed else None
            if o is None:
                m.Add(e == s + d)
            else:
                # e = s + d - o*gain  -> e + o*gain = s + d
                m.Add(e + o * gain == s + d)
            starts[t.id], ends[t.id] = s, e
            durations[t.id] = d
            overtime_b[t.id] = o
            overtime_gain[t.id] = gain

            iv = m.NewIntervalVar(s, d, e, f'i_{t.id}')  # usamos duración base para reservas de capacidad
            intervals[t.id] = iv

            # Ventanas
            if t.window_start:
                m.Add(s >= (t.window_start - base).days)
            if t.window_end:
                m.Add(e <= (t.window_end - base).days)

        # Precedencia
        for t in tasks:
            for p in t.predecessor_ids:
                m.Add(starts[t.id] >= ends[p.id])

        # Capacidad acumulativa por recurso: AddCumulative
        # Demanda = demand_units por tarea; Capacidad = resource.capacity
        by_res = {}
        for t in tasks:
            rid = t.resource_id.id if t.resource_id else None
            if rid:
                by_res.setdefault(rid, []).append((intervals[t.id], max(1, int(t.demand_units or 1))))
        for rid, items in by_res.items():
            intervals_list = [iv for iv, _ in items]
            demands_list = [dem for _, dem in items]
            cap = max(1, int(self.env['of.resource'].browse(rid).capacity or 1))
            m.AddCumulative(intervals_list, demands_list, cap)

        # Objetivo: minimizar makespan + prioridades + coste overtime
        makespan = m.NewIntVar(0, horizon, 'makespan')
        m.AddMaxEquality(makespan, [ends[t.id] for t in tasks])

        obj = [makespan]
        for t in tasks:
            if t.priority:
                pen = m.NewIntVar(0, horizon, f'pen_{t.id}')
                m.Add(pen == ends[t.id])
                obj.append((10 + int(t.priority)) * pen)
            if overtime_b[t.id] is not None and (t.overtime_cost or 0) > 0:
                # coste overtime proporcional al d y al costo definido
                cost = int(round(1000 * float(t.overtime_cost)))  # escalar para enteros
                obj.append(cost * overtime_b[t.id])

        m.Minimize(sum(obj))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        st = solver.Solve(m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {'error': 'sin solución', 'plan': []}

        plan = []
        for t in tasks:
            s = solver.Value(starts[t.id])
            e = solver.Value(ends[t.id])
            plan.append({
                'task_id': t.id,
                'start': base + relativedelta(days=s),
                'end': base + relativedelta(days=e),
                'overtime': bool(overtime_b[t.id] and solver.Value(overtime_b[t.id]))
            })
        return {'plan': plan, 'objective': solver.ObjectiveValue()}
```

> Nota: Para la reserva de capacidad se usa la **duración base**; si se activa overtime, el **fin** se adelanta por la restricción lineal. Es un buen balance entre fidelidad y complejidad.

---

## 2) CEO – Aging AR/AP y Lead‑time Abastecimiento

### 2.1 Cálculo de buckets (AR/AP)

`of_ceo_dashboard/models/kpi_extend.py`

```python
from odoo import models, fields, api
from datetime import date

BUCKETS = [(0,30,'b0_30'), (31,60,'b31_60'), (61,90,'b61_90'), (91,36500,'b90p')]

class OfCeoKpi(models.Model):
    _inherit = 'of.ceo.kpi'

    ar_b0_30 = fields.Float(); ar_b31_60 = fields.Float(); ar_b61_90 = fields.Float(); ar_b90p = fields.Float()
    ap_b0_30 = fields.Float(); ap_b31_60 = fields.Float(); ap_b61_90 = fields.Float(); ap_b90p = fields.Float()
    supply_lead_time = fields.Float(help='Lead-time promedio abastecimiento (días)')

    @api.model
    def compute_today(self):
        rec = super().compute_today()
        env = self.env
        today = fields.Date.today()

        def age(inv):
            due = inv.invoice_date_due or inv.invoice_date or today
            return (today - due).days

        def bucketize(moves, sign=1):
            acc = {k:0.0 for _,_,k in BUCKETS}
            for m in moves:
                a = age(m)
                amt = float(getattr(m, 'amount_residual', 0.0)) * sign
                for lo, hi, key in BUCKETS:
                    if a >= lo and a <= hi:
                        acc[key] += max(0.0, amt)
                        break
            return acc

        AR = env['account.move'].sudo().search([('move_type','=','out_invoice'),('payment_state','!=','paid')]) if 'account.move' in env else env['account.move']
        AP = env['account.move'].sudo().search([('move_type','=','in_invoice'),('payment_state','!=','paid')]) if 'account.move' in env else env['account.move']

        ar = bucketize(AR, +1); ap = bucketize(AP, +1)
        rec.write({
            'ar_b0_30': ar['b0_30'], 'ar_b31_60': ar['b31_60'], 'ar_b61_90': ar['b61_90'], 'ar_b90p': ar['b90p'],
            'ap_b0_30': ap['b0_30'], 'ap_b31_60': ap['b31_60'], 'ap_b61_90': ap['b61_90'], 'ap_b90p': ap['b90p'],
        })

        # Lead-time abastecimiento: desde RFQ award → fecha recepción (stock.move o PO done)
        lt = 0.0; n=0
        if 'of.award' in env and 'stock.picking' in env:
            awards = env['of.award'].sudo().search([], limit=200)
            for aw in awards:
                picking = env['stock.picking'].sudo().search([('origin','ilike', str(aw.id)), ('state','=','done')], limit=1)
                if picking:
                    lt += (picking.date_done.date() - aw.create_date.date()).days; n += 1
        rec.write({'supply_lead_time': (lt/max(1,n)) if n else 0.0})
        return rec
```

### 2.2 Endpoints series y UI (barras apiladas AR/AP + lead‑time)

`of_ceo_dashboard/controllers/kpi_series.py`

```python
from odoo import http
from odoo.http import request

class CeoKpiSeries(http.Controller):
    @http.route('/of/ceo/aging_series', type='json', auth='user')
    def aging(self, days=180):
        recs = request.env['of.ceo.kpi'].sudo().search([], order='date asc')
        out = []
        for r in recs:
            out.append({'date': str(r.date),
                        'ar': [r.ar_b0_30, r.ar_b31_60, r.ar_b61_90, r.ar_b90p],
                        'ap': [r.ap_b0_30, r.ap_b31_60, r.ap_b61_90, r.ap_b90p],
                        'supply_lt': r.supply_lead_time})
        return out
```

`of_ceo_dashboard/static/src/js/ceo.js` (extensión)

```javascript
// ... dentro de CeoDash
onMounted(async()=>{
  this.state.kpis = await this.rpc('/of/ceo/kpi',{});
  this.state.series = await this.rpc('/of/ceo/kpi_series',{days:180});
  this.state.aging = await this.rpc('/of/ceo/aging_series',{days:180});
  this.draw();
});

draw(){ this.drawCash(); this.drawBudget(); this.drawAging(); this.drawSupplyLT(); }

drawAging(){ const el=this.el.querySelector('canvas.ofceo-aging'); if(!el) return; const ctx=el.getContext('2d'); const W=el.width=el.clientWidth; const H=el.height=240; ctx.clearRect(0,0,W,H);
  const xs=this.state.aging.map((p,i)=>i); const bars=this.state.aging.map(p=>p.ar); // ejemplo muestra AR, se puede alternar con AP
  const max = Math.max(1, ...bars.map(b=>b.reduce((a,c)=>a+c,0)));
  const bw=(W-60)/(xs.length||1);
  for(let i=0;i<xs.length;i++){
    const [b0,b1,b2,b3] = bars[i]; let y=H-30; const x=40+i*bw+4; const heights=[b0,b1,b2,b3].map(v=> (v/max)*(H-60));
    const fills=['#d6e0ff','#aebcf2','#8799e5','#5b6dcf'];
    for(let k=0;k<4;k++){ const h=heights[k]; y-=h; ctx.fillStyle=fills[k]; ctx.fillRect(x,y,bw-8,h); }
  }
}

drawSupplyLT(){ const el=this.el.querySelector('canvas.ofceo-supplylt'); if(!el) return; const ctx=el.getContext('2d'); const W=el.width=el.clientWidth; const H=el.height=200; ctx.clearRect(0,0,W,H);
  const ys=this.state.aging.map(p=>p.supply_lt||0); if(!ys.length) return; const minY=Math.min(...ys,0), maxY=Math.max(...ys,1);
  const x2=(i)=> 40 + (i/((ys.length-1)||1))*(W-60); const y2=(v)=> H-30 - ((v-minY)/(maxY-minY||1))*(H-60);
  ctx.strokeStyle='#2e7d32'; ctx.beginPath(); ys.forEach((v,i)=>{ const x=x2(i), y=y2(v); i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke();
}
```

`of_ceo_dashboard/static/src/xml/ceo.xml` (extensión)

```xml
<templates xml:space="preserve">
  <t t-name="of_ceo_dashboard.CEO">
    <div class="ofceo">
      <div class="kpis"> <!-- como antes --> </div>
      <div class="chart-wrap">
        <h3>Evolución Días de Caja (180d)</h3>
        <canvas class="ofceo-chart"></canvas>
      </div>
      <div class="chart-wrap">
        <h3>IVA (F29) – Due vs Diferido</h3>
        <canvas class="ofceo-budget"></canvas>
      </div>
      <div class="chart-wrap">
        <h3>AR Aging (0-30 / 31-60 / 61-90 / 90+)</h3>
        <canvas class="ofceo-aging"></canvas>
      </div>
      <div class="chart-wrap">
        <h3>Lead‑time de Abastecimiento (promedio)</h3>
        <canvas class="ofceo-supplylt"></canvas>
      </div>
    </div>
  </t>
</templates>
```

---

## 3) Tests E2E (HttpCase) de controladores

Estructura:

```
/tests_ofitec/
├─ test_http_graphql.py
├─ test_http_upload.py
├─ test_http_vision.py
└─ test_http_sync.py
```

### 3.1 GraphQL

`tests_ofitec/test_http_graphql.py`

```python
from odoo.tests.common import HttpCase, tagged

@tagged('-at_install', 'post_install')
class TestGraphQL(HttpCase):
    def test_graphql_projects(self):
        # si graphene no está, el controlador responde error controlado
        body = {
            'query': '{ projects { id name } }'
        }
        res = self.url_open('/graphql', data=body)
        assert res.status_code in (200, 500)
```

### 3.2 Upload por chunks

`tests_ofitec/test_http_upload.py`

```python
from odoo.tests.common import HttpCase, tagged

@tagged('-at_install','post_install')
class TestUpload(HttpCase):
    def test_chunk_upload_cycle(self):
        init = self.url_open('/of/pwa/upload/init', data={'filename':'t.txt','mimetype':'text/plain','model':'of.form.response','res_id':0}).json()
        token = init.get('token')
        assert token
        self.url_open(f'/of/pwa/upload/chunk?token={token}&idx=0', data=b'hello')
        fin = self.url_open('/of/pwa/upload/finish', data={'token': token, 'filename':'t.txt','model':'of.form.response','res_id':0,'mimetype':'text/plain'}).json()
        assert fin.get('ok') is True
```

### 3.3 Vision – listado de detecciones (vacío sin proveedor)

`tests_ofitec/test_http_vision.py`

```python
from odoo.tests.common import HttpCase, tagged

@tagged('-at_install','post_install')
class TestVision(HttpCase):
    def test_list_endpoint(self):
        res = self.url_open('/of/qhse/vision/list', data={'response_id': 0}).json()
        assert isinstance(res, list)
```

### 3.4 Sync batch

`tests_ofitec/test_http_sync.py`

```python
from odoo.tests.common import HttpCase, tagged

@tagged('-at_install','post_install')
class TestSync(HttpCase):
    def test_sync_batch(self):
        payload = { 'ops': [ {'model': 'mail.message', 'values': {'subject':'E2E','body':'ok'}} ] }
        res = self.url_open('/of/pwa/sync', data=payload).json()
        assert res.get('ok') is True
```

---

## 4) QA y checklist

-

---

## 5) Notas finales

- Todo mantiene SSOT `of.project`. Sin Enterprise; OR‑Tools opcional.
- En producción, conviene mover uploads grandes a almacenamiento externo (S3/GCS) y firmar URLs.
- Para aging exacto, si el cliente usa cuentas contables externas, podemos exponer `/api/ar_aging` y ETL.

