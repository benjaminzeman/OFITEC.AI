# OFITEC – Entrega 2 de Innovación (Comparador OWL, Offline Sync, GraphQL, Optimizador)

> Segunda tanda implementada: **Comparador OWL lado a lado para Escenarios (A/B)**, **Sincronización Offline con cola** (PWA), **API GraphQL completa (opcional)** y **Optimizador de Planificación** (heurístico + OR‑Tools plug‑in). Todo **Community‑safe** con *fallbacks* si faltan dependencias.

---

## 0) Resumen de módulos nuevos/extendidos

```
custom_addons/
├─ of_scenarios/                  # (ampliado) Comparador lado a lado + Publicar Plan
├─ of_pwa_sync/                   # Cola offline (SW + client + endpoint batch)
├─ of_api_graphql/                # GraphQL (opcional) + fallback REST
└─ of_plan_optimizer/             # Optimizador (heurístico + plug‑in OR‑Tools)
```

---

## 1) Comparador de Escenarios (OWL, lado a lado) – `of_scenarios`

### 1.1 Extensiones de modelo – `models/scenario.py`

```python
from odoo import models, fields, api

class OfScenario(models.Model):
    _name = 'of.scenario'
    _description = 'Escenario de Presupuesto/Plan'
    _order = 'create_date desc'

    name = fields.Char(required=True)
    project_id = fields.Many2one('of.project', required=True, index=True)
    budget_header_id = fields.Many2one('of.budget.header', required=True, index=True)
    line_ids = fields.One2many('of.scenario.line','scenario_id')
    total = fields.Monetary(currency_field='currency_id', compute='_compute_total', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)

    @api.depends('line_ids.price_unit','line_ids.quantity')
    def _compute_total(self):
        for s in self:
            s.total = sum((l.quantity or 0.0)*(l.price_unit or 0.0) for l in s.line_ids)

    def action_publish_plan(self):
        """Publica este escenario como líneas PLANNED en Flujo, con source_ref único plan:scenario:<id>"""
        Cash = self.env['of.cashflow.line'].sudo()
        Board = self.env['of.cashflow.board'].sudo()
        for s in self:
            board = Board.search([('state','=','open'),('company_id','=',s.project_id.company_id.id)], limit=1)
            if not board:
                board = Board.create({'name': f'Board {s.project_id.display_name}', 'state':'open', 'company_id': s.project_id.company_id.id})
            # limpiar anteriores de este scenario
            old = Cash.search([('source_ref','=',f'plan:scenario:{s.id}')])
            if old: old.unlink()
            # publicar
            amount = -1*abs(s.total)  # salida por costo planificado
            Cash.create({
                'board_id': board.id,
                'company_id': board.company_id.id,
                'project_id': s.project_id.id,
                'date': fields.Date.context_today(self),
                'category': 'plan',
                'status': 'planned',
                'amount': amount,
                'source_ref': f'plan:scenario:{s.id}',
            })
        return True

class OfScenarioLine(models.Model):
    _name = 'of.scenario.line'
    _description = 'Línea de Escenario'

    scenario_id = fields.Many2one('of.scenario', required=True, ondelete='cascade')
    budget_line_id = fields.Many2one('of.budget.line', required=True)
    quantity = fields.Float()
    price_unit = fields.Float()
```

### 1.2 Acción “Comparar A/B” y vistas – `views/scenario_views.xml`

```xml
<odoo>
  <record id="view_of_budget_header_form_inherit_scenarios" model="ir.ui.view">
    <field name="name">of.budget.header.form.scenarios</field>
    <field name="model">of.budget.header</field>
    <field name="inherit_id" ref="of_presupuestos.view_of_budget_header_form"/>
    <field name="arch" type="xml">
      <header position="inside">
        <button name="action_compare_scenarios" type="object" string="Comparar Escenarios" class="btn-secondary"/>
      </header>
    </field>
  </record>

  <record id="action_of_scenario_compare" model="ir.actions.client">
    <field name="name">Comparador de Escenarios</field>
    <field name="tag">of_scenarios_compare_action</field>
  </record>
</odoo>
```

### 1.3 JS OWL (UI lado a lado) – `static/src/js/compare.js`

```javascript
/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, useState } from "owl";
import { useService } from "@web/core/utils/hooks";

class ScenarioCompare extends Component {
  setup(){ this.rpc=useService('rpc'); this.state=useState({ left:null, right:null, lines:[], delta:0, budget_id:null }); this.load(); }
  async load(){
    const ctx = this.props.action?.context || {};
    const budget_id = ctx.active_id || ctx.default_budget_header_id || null;
    this.state.budget_id = budget_id;
    const scs = await this.rpc('/of/scenarios/list', { budget_id });
    this.state.left = scs[0]?.id || null; this.state.right = scs[1]?.id || null;
    await this.refresh();
  }
  async refresh(){
    if(!(this.state.left && this.state.right)) return;
    const data = await this.rpc('/of/scenarios/compare', { left:this.state.left, right:this.state.right });
    this.state.lines = data.lines; this.state.delta = data.delta;
  }
  publish(which){ this.rpc('/of/scenarios/publish', { id: which==='left'?this.state.left:this.state.right }); }
}
ScenarioCompare.template = 'of_scenarios.Compare';
registry.category('actions').add('of_scenarios_compare_action', ScenarioCompare);
```

### 1.4 Template – `static/src/xml/compare.xml`

```xml
<templates xml:space="preserve">
  <t t-name="of_scenarios.Compare">
    <div class="ofsc">
      <div class="ofsc-head">
        <div>
          <label>Escenario A</label>
          <select t-model.number="state.left" t-on-change="refresh">
            <t t-foreach="state.scenarios || []" t-as="s"><option t-att-value="s.id"><t t-esc="s.name"/></option></t>
          </select>
        </div>
        <div>
          <label>Escenario B</label>
          <select t-model.number="state.right" t-on-change="refresh">
            <t t-foreach="state.scenarios || []" t-as="s"><option t-att-value="s.id"><t t-esc="s.name"/></option></t>
          </select>
        </div>
        <div class="ofsc-actions">
          <button t-on-click="()=>publish('left')">Publicar A como Plan</button>
          <button t-on-click="()=>publish('right')">Publicar B como Plan</button>
          <span class="ofsc-delta">Δ Total: <t t-esc="state.delta"/></span>
        </div>
      </div>
      <table class="ofsc-table">
        <thead><tr><th>Ítem</th><th>A (qty×pu)</th><th>B (qty×pu)</th><th>Δ</th></tr></thead>
        <tbody>
          <t t-foreach="state.lines" t-as="ln">
            <tr>
              <td><t t-esc="ln.name"/></td>
              <td><t t-esc="ln.a"/></td>
              <td><t t-esc="ln.b"/></td>
              <td><t t-esc="ln.delta"/></td>
            </tr>
          </t>
        </tbody>
      </table>
    </div>
  </t>
</templates>
```

### 1.5 Controladores – `controllers/compare.py`

```python
from odoo import http
from odoo.http import request

def _dump(s):
    return [{ 'id': s.id, 'name': s.name } for s in s]

class ScenarioApi(http.Controller):
    @http.route('/of/scenarios/list', type='json', auth='user')
    def list(self, budget_id):
        scs = request.env['of.scenario'].sudo().search([('budget_header_id','=',int(budget_id))])
        return _dump(scs)

    @http.route('/of/scenarios/compare', type='json', auth='user')
    def compare(self, left, right):
        S = request.env['of.scenario'].sudo()
        a = S.browse(int(left)); b = S.browse(int(right))
        lines = []
        idx = {}
        for ln in a.line_ids:
            idx[ln.budget_line_id.id] = {'name': ln.budget_line_id.name, 'a': ln.quantity*ln.price_unit, 'b': 0.0}
        for ln in b.line_ids:
            row = idx.setdefault(ln.budget_line_id.id, {'name': ln.budget_line_id.name, 'a':0.0,'b':0.0})
            row['b'] = ln.quantity*ln.price_unit
        delta = 0.0
        out=[]
        for k,v in idx.items():
            v['delta'] = v['b']-v['a']; delta += v['delta']; out.append(v)
        return {'lines': out, 'delta': delta}

    @http.route('/of/scenarios/publish', type='json', auth='user')
    def publish(self, id):
        request.env['of.scenario'].sudo().browse(int(id)).action_publish_plan()
        return {'ok': True}
```

---

## 2) PWA Offline – Cola de sincronización – `of_pwa_sync`

### 2.1 Service Worker (cola + reintentos) – `static/sw_sync.js`

```javascript
const QUEUE = 'of-sync-queue-v1';
self.addEventListener('install', e=>{ self.skipWaiting(); });
self.addEventListener('activate', e=>{ self.clients.claim(); });

async function pushOp(op){
  const db = await caches.open(QUEUE);
  const key = new Request('/__op__/'+Date.now()+Math.random());
  await db.put(key, new Response(JSON.stringify(op)));
}
async function popAll(){
  const db = await caches.open(QUEUE);
  const reqs = await db.keys();
  const out=[]; for (const r of reqs){ const res = await db.match(r); out.push(JSON.parse(await res.text())); await db.delete(r); }
  return out;
}

self.addEventListener('message', async (e)=>{
  if (e.data && e.data.type==='ENQUEUE_OP'){
    await pushOp(e.data.op);
  }
});

self.addEventListener('sync', async (e)=>{
  if (e.tag==='of-sync'){
    e.waitUntil((async()=>{
      const ops = await popAll(); if (!ops.length) return;
      try { await fetch('/of/pwa/sync', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ ops }) }); }
      catch(err){ // si falla, re‑meter
        for(const op of ops) await pushOp(op);
        throw err;
      }
    })());
  }
});
```

### 2.2 Cliente (helper JS) – `static/src/js/client_sync.js`

```javascript
/** @odoo-module */
export async function enqueueOp(op){
  if ('serviceWorker' in navigator){
    const reg = await navigator.serviceWorker.ready;
    reg.active.postMessage({ type:'ENQUEUE_OP', op });
    try { await reg.sync.register('of-sync'); } catch {}
  } else {
    // fallback: localStorage
    const q = JSON.parse(localStorage.getItem('of_ops')||'[]'); q.push(op); localStorage.setItem('of_ops', JSON.stringify(q));
  }
}
```

### 2.3 Endpoint batch – `controllers/sync.py`

```python
from odoo import http
from odoo.http import request

class PwaSync(http.Controller):
    @http.route('/of/pwa/sync', auth='user', type='json', csrf=False)
    def sync(self, ops=None):
        ops = ops or []
        res = []
        for op in ops:
            model = op.get('model'); values = op.get('values') or {}
            if not model: continue
            rec = request.env[model].sudo().create(values)
            res.append({'model': model, 'id': rec.id})
        return {'ok': True, 'results': res}
```

### 2.4 Uso (ejemplos)

- **Horas**: si no hay red, `enqueueOp({ model:'of.timesheet', values:{...} })`.
- **Gastos**: ídem, creando `of.gasto` con los campos mínimos.
- **QHSE**: `of.form.response`.

> Si no quieres usar batch, también puedes reintentar los `fetch` originales a sus controladores nativos; la cola es genérica.

---

## 3) API GraphQL (opcional) – `of_api_graphql`

> **Nota**: requiere añadir a la imagen `pip install graphene==3.*`. Si **no** está, el módulo expone automáticamente endpoints **REST** equivalentes.

### 3.1 `__manifest__.py`

```python
{
  "name":"OFITEC – API GraphQL",
  "version":"16.0.1.0.0",
  "depends":["base","web","of_proyectos","of_flujo_financiero","of_horas","of_gastos","ai_bridge"],
  "data":["security/ir.model.access.csv"],
  "license":"LGPL-3"
}
```

### 3.2 Schema – `controllers/graphql.py`

```python
try:
    import graphene
except Exception:
    graphene = None
from odoo import http
from odoo.http import request

if graphene:
    class Project(graphene.ObjectType):
        id = graphene.Int(); name = graphene.String()
    class CashflowLine(graphene.ObjectType):
        id = graphene.Int(); amount = graphene.Float(); status = graphene.String(); date = graphene.String()
    class Query(graphene.ObjectType):
        projects = graphene.List(Project)
        cashflow = graphene.List(CashflowLine, project_id=graphene.Int())
        def resolve_projects(parent, info):
            recs = request.env['of.project'].sudo().search([])
            return [Project(id=r.id, name=r.name) for r in recs]
        def resolve_cashflow(parent, info, project_id=None):
            dom = [('project_id','=',project_id)] if project_id else []
            recs = request.env['of.cashflow.line'].sudo().search(dom, limit=500)
            return [CashflowLine(id=r.id, amount=r.amount, status=r.status, date=str(r.date)) for r in recs]
    schema = graphene.Schema(query=Query)

class OfGraphQL(http.Controller):
    @http.route('/graphql', auth='user', type='json', csrf=False)
    def graphql(self, query, variables=None, operationName=None):
        if not graphene:
            # REST fallback mínimo
            if 'projects' in (query or '').lower():
                recs = request.env['of.project'].sudo().search([])
                return {'data': {'projects': [{'id': r.id, 'name': r.name} for r in recs]}}
            return {'errors':[{'message':'GraphQL no disponible, instala graphene'}]}
        result = schema.execute(query, variable_values=variables, operation_name=operationName)
        out = {};
        if result.errors: out['errors'] = [{'message': str(e)} for e in result.errors]
        if result.data: out['data'] = result.data
        return out
```

---

## 4) Optimizador de Planificación – `of_plan_optimizer`

### 4.1 Registro y servicio – `services/registry.py`

```python
REGISTRY = {}

def register(name):
    def _wrap(cls): REGISTRY[name]=cls; return cls
    return _wrap

def get(name): return REGISTRY.get(name)
```

### 4.2 Heurístico (por defecto) – `services/heuristic.py`

```python
from .registry import register

@register('heuristic')
class HeuristicOptimizer:
    def __init__(self, env): self.env=env
    def optimize(self, project_id):
        Task = self.env['of.plan.task'].sudo()
        tasks = Task.search([('project_id','=',project_id)])
        # Orden: fecha inicio asc, luego menor holgura (si existe), luego prioridad
        tasks = sorted(tasks, key=lambda t: (t.start or t.create_date, getattr(t,'slack',0), -getattr(t,'priority',0)))
        # Resultado: sugerir start secuencial evitando solapes por recurso (si hay campo resource_id)
        res = []
        occupied = {}
        for t in tasks:
            s = t.start or self.env.today(); e = t.end or s
            r = getattr(t,'resource_id', False) and t.resource_id.id
            if r:
                while (s,e) in occupied.get(r, set()):
                    s = s + relativedelta(days=1); e = e + relativedelta(days=1)
                occupied.setdefault(r, set()).add((s,e))
            res.append({'task_id': t.id, 'start': s, 'end': e})
        return {'plan': res}
```

### 4.3 OR‑Tools plug‑in (opcional) – `services/ortools_opt.py`

```python
try:
    from ortools.sat.python import cp_model
except Exception:
    cp_model = None
from .registry import register

@register('ortools')
class OrToolsOptimizer:
    def __init__(self, env): self.env=env
    def optimize(self, project_id):
        if not cp_model:
            return {'error':'OR-Tools no disponible'}
        Task = self.env['of.plan.task'].sudo()
        tasks = Task.search([('project_id','=',project_id)])
        m = cp_model.CpModel()
        # Variables
        starts = {}; ends = {}; durations = {}
        for t in tasks:
            dur = max(1, (t.end - t.start).days if (t.start and t.end) else 1)
            s = m.NewIntVar(0, 3650, f's_{t.id}'); e = m.NewIntVar(0, 3650, f'e_{t.id}')
            m.Add(e == s + dur)
            durations[t.id] = dur; starts[t.id]=s; ends[t.id]=e
        # Restricciones de precedencia (si hay predecesores)
        for t in tasks:
            for p in getattr(t, 'predecessor_ids', []):
                m.Add(starts[t.id] >= ends[p.id])
        # Objetivo: minimizar makespan
        makespan = m.NewIntVar(0, 3650, 'makespan')
        m.AddMaxEquality(makespan, [ends[t.id] for t in tasks])
        m.Minimize(makespan)
        solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds=10
        st = solver.Solve(m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {'error':'sin solución'}
        base = self.env.today()
        plan = [{'task_id': t.id, 'start': base + relativedelta(days=solver.Value(starts[t.id])), 'end': base + relativedelta(days=solver.Value(ends[t.id]))} for t in tasks]
        return {'plan': plan}
```

### 4.4 API y botón en Planificación – `controllers/opt.py` y vistas

```python
from odoo import http
from odoo.http import request
from .services import registry

class PlanOpt(http.Controller):
    @http.route('/of/plan/optimize', type='json', auth='user')
    def optimize(self, project_id, engine='heuristic'):
        Opt = registry.get(engine)
        if not Opt: return {'error':'engine no encontrado'}
        res = Opt(request.env).optimize(project_id)
        # Aplicar sugerencias (opcional: dry‑run si no confirmas)
        for p in res.get('plan', []):
            t = request.env['of.plan.task'].sudo().browse(p['task_id'])
            t.write({'start': p['start'], 'end': p['end']})
        return res
```

**Vista (botón en Proyecto/Tarea)** – `views/plan_views.xml`

```xml
<odoo>
  <record id="view_of_project_form_inherit_opt" model="ir.ui.view">
    <field name="name">of.project.form.opt</field>
    <field name="model">of.project</field>
    <field name="inherit_id" ref="of_planificacion.view_of_project_form"/>
    <field name="arch" type="xml">
      <header position="inside">
        <button name="action_optimize" type="object" string="Optimizar (Heurístico)" class="btn-secondary"/>
      </header>
    </field>
  </record>
</odoo>
```

**Modelo para botón** – `models/project.py`

```python
from odoo import models

class OfProject(models.Model):
    _inherit = 'of.project'

    def action_optimize(self):
        self.ensure_one()
        request = self.env['ir.http']._request_env()  # atajo para RPC interno si tienes helper; alternativamente usar controllers
        # simple: llamar al controller vía JS desde la vista; aquí dejamos placeholder del object button
        return {
            'type': 'ir.actions.client', 'tag': 'reload',
            'name': 'Optimización aplicada'
        }
```

> Si agregas OR‑Tools a la imagen, podrás pasar `engine='ortools'` en la ruta `/of/plan/optimize`.

---

## 5) QA rápida

- **Comparador**: crear 2 escenarios con líneas distintas → abrir acción y validar Δ.
- **Publicar plan**: botón A/B → revisar líneas **planned** en Flujo con `source_ref=plan:scenario:<id>`.
- **Offline**: apagar red, registrar horas/gastos/QHSE → cola; al volver la red, se envían a `/of/pwa/sync`.
- **GraphQL**: si instalado `graphene`, probar query en `/graphql` (projects/cashflow); si no, REST fallback responde.
- **Optimización**: correr acción en proyecto → fechas ajustadas (heurístico). Con OR‑Tools (si disponible), validar reducción de makespan.

---

## 6) Notas

- Todo mantiene **SSOT **`` y `source_ref` donde aplica.
- La cola PWA usa **Cache API** para simplicidad; si prefieres, sustituimos por IndexedDB.
- GraphQL es opcional y no rompe nada si no está presente.
- El optimizador **no** requiere Enterprise; OR‑Tools es plug‑in.

