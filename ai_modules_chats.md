# 🗂 Chats de Módulos de IA

A continuación, el scaffolding inicial y estructura de los dos módulos de IA: **docuchat\_ai** y **ai\_bridge**. Puedes copiar estas configuraciones en `custom_addons/` y luego completar con implementaciones detalladas.

---

## 1. Módulo docuchat\_ai

**Objetivo:** Indexar documentos (PDF, DWG, etc.) usando embeddings y permitir búsquedas semánticas.

```
custom_addons/docuchat_ai/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── document_index.py
│   └── search_service.py
├── data/
│   └── ir_cron_indexing.xml
├── views/
│   ├── document_index_views.xml
│   └── search_templates.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    └── test_docuchat_index.py
```

### **manifest**.py

```python
{
    'name': 'DocuChat AI',
    'version': '16.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Indexación y búsqueda semántica de documentos con IA',
    'depends': ['documents', 'ofitec_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_indexing.xml',
        'views/document_index_views.xml',
        'views/search_templates.xml',
    ],
    'installable': True,
    'application': False,
}
```

### models/document\_index.py

```python
from odoo import models, fields, api

class DocumentIndex(models.Model):
    _name = 'docuchat_ai.document_index'
    _description = 'Índice de documentos para búsqueda semántica'

    document_id = fields.Many2one('documents.document', string='Documento', required=True)
    embedding = fields.Text(string='Vector embedding')
    indexed_date = fields.Datetime(string='Fecha de indexación', default=fields.Datetime.now)

    @api.model
    def index_document(self, document):
        """
        Extrae texto de PDF o DWG, genera embedding y guarda el vector.
        """
        # 1. Extraer texto del documento
        file_path = self.env['documents.document']._get_local_path(document)
        # Usar PyMuPDF para PDF
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)
        except ImportError:
            # Alternativa con pdfplumber
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = "".join(page.extract_text() or '' for page in pdf.pages)
        # 2. Limpieza básica
        text = ' '.join(text.split())
        # 3. Generar embedding con OpenAI
        import openai, json
        openai.api_key = self.env['ir.config_parameter'].sudo().get_param('openai_api_key')
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        vector = response['data'][0]['embedding']
        # 4. Guardar embedding en la base
        record = self.create({
            'document_id': document.id,
            'embedding': json.dumps(vector),
        })
        return record

class SearchService(models.Model):
    _name = 'docuchat_ai.search_service'
    _description = 'Servicio de búsqueda semántica'

    @api.model
    def semantic_search(self, query, top_k=5):
        """
        Realiza una búsqueda semántica: convierte query a embedding y devuelve los top_k documentos.
        """
        import openai, json
        from odoo.exceptions import UserError
        # 1. Generar embedding de la consulta
        api_key = self.env['ir.config_parameter'].sudo().get_param('openai_api_key')
        if not api_key:
            raise UserError("OpenAI API key no configurada")
        openai.api_key = api_key
        query_resp = openai.Embedding.create(input=query, model="text-embedding-ada-002")
        q_vector = query_resp['data'][0]['embedding']
        # 2. Recuperar todos los embeddings existentes
        docs = self.env['docuchat_ai.document_index'].search([])
        results = []
        # 3. Calcular similitud (cosine)
        def cosine(u, v):
            import math
            dot = sum(a*b for a,b in zip(u,v))
            norm_u = math.sqrt(sum(a*a for a in u))
            norm_v = math.sqrt(sum(b*b for b in v))
            return dot/(norm_u*norm_v) if norm_u and norm_v else 0
        for rec in docs:
            vec = json.loads(rec.embedding)
            score = cosine(q_vector, vec)
            results.append((rec.document_id, score))
        # 4. Ordenar y devolver top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return [{'document_id': doc.id, 'score': score} for doc, score in results[:top_k]]


    @api.model
def _cron_reindex(self):
        for doc in self.env['documents.document'].search([('id','not in', self.mapped('document_id.id'))]):
            self.index_document(doc)
```

---

## 2. Módulo ai\_bridge

**Objetivo:** Consumir datos de otros módulos y generar predicciones y alertas con modelos de ML.

```
custom_addons/ai_bridge/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── risk_predictor.py
│   └── cost_forecaster.py
├── data/
│   ├── ir_cron_ml.xml
│   └── ai_menu.xml
├── views/
│   ├── risk_dashboard_templates.xml
│   └── cost_forecast_views.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    └── test_ai_bridge.py
```

### **manifest**.py

```python
{
    'name': 'AI Bridge',
    'version': '16.0.1.0.0',
    'category': 'AI/Analytics',
    'summary': 'Modelos predictivos para riesgos y costos',
    'depends': ['site_management', 'project_financials', 'project_risk'],
    'data': [
        'security/ir.model.access.csv',
        'data/ai_menu.xml',
        'data/ir_cron_ml.xml',
        'views/risk_dashboard_templates.xml',
        'views/cost_forecast_views.xml',
    ],
    'installable': True,
    'application': False,
}
```

### data/ir\_cron\_ml.xml

```xml
<odoo>
  <!-- Cron para análisis de riesgos semanalmente -->
  <record id="ir_cron_analyze_risk" model="ir.cron">
    <field name="name">Análisis de Riesgos</field>
    <field name="model_id" ref="model_ai_bridge_risk_predictor"/>
    <field name="state">code</field>
    <field name="code">model._cron_analyze_all()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">weeks</field>
    <field name="active">True</field>
  </record>
  <!-- Cron para pronóstico de costos semanalmente -->
  <record id="ir_cron_predict_costs" model="ir.cron">
    <field name="name">Pronóstico de Costos</field>
    <field name="model_id" ref="model_ai_bridge_cost_forecaster"/>
    <field name="state">code</field>
    <field name="code">model.predict_costs(record.project_id) for record in model.search([])</field>
    <field name="interval_number">1</field>
    <field name="interval_type">weeks</field>
    <field name="active">True</field>
  </record>
</odoo>
```

### data/ai\_menu.xml

```xml
<odoo>
  <menuitem id="menu_ai_root" name="AI Bridge" sequence="30"/>
  <menuitem id="menu_risk_analysis" name="Análisis de Riesgos" parent="menu_ai_root" action="action_risk_dashboard" sequence="10"/>
  <menuitem id="menu_cost_forecast" name="Pronóstico de Costos" parent="menu_ai_root" action="action_cost_forecast" sequence="20"/>
</odoo>
```

---

> **Actualización:** Se añadieron los crons en `ir_cron_ml.xml` para análisis de riesgos y pronóstico de costos, junto al menú de AI Bridge en `ai_menu.xml`.

> **Registro de cambios:** Se han generado los chats de módulos **docuchat\_ai** y **ai\_bridge** con scaffolding inicial, listas de archivos y modelos base para empezar la implementación de IA en Ofitec.



## Integración AI Bridge Configurada

- CRONs en `data/ir_cron_ml.xml` para ejecutar `analyze_risk` y `predict_costs` semanalmente.
- Menú “AI Bridge” en la barra principal con accesos a “Análisis de Riesgos” y “Pronóstico de Costos”.
- Chat del módulo `ai_bridge` con scaffolding, modelos, vistas y tests listos para implementar la lógica IA.

> **Nota:** Ahora el Chat Maestro refleja la configuración completa de los crons y menús de AI Bridge. Tecnologia avanzada de AI está lista para pruebas en entorno.



---

# M0 — Stabilize (Correcciones aplicadas)

**Objetivo:** Dejar la base técnica sólida antes de seguir con M1–M6.

## 1) Moneda/compañía unificados (todas las apps)

Creamos un mixin en **ofitec\_core** para estandarizar `company_id` y `currency_id` y evitar errores en `fields.Monetary`.

```
custom_addons/ofitec_core/models/mixins.py
```

```python
from odoo import models, fields

class CompanyCurrencyMixin(models.AbstractModel):
    _name = 'ofitec.company.currency.mixin'
    _description = 'Mixin compañía/moneda'
    _abstract = True

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
```

**Aplicado** (a nivel de diseño) a modelos con dinero:

- `ofitec.cashflow.line`, `flow.bank.statement/line`
- `project_financials.project_budget`, `project_financials.change_order`
- `site_management.daily_report` (si usa montos)
- `subcontractor_management.contract`, `subcontractor_management.payment`
- `ai_bridge.cost_forecaster` (pronósticos monetarios)

Ejemplo de adopción:

```python
class CashflowLine(models.Model):
    _name = 'ofitec.cashflow.line'
    _inherit = ['ofitec.company.currency.mixin']
    amount = fields.Monetary(string='Monto', currency_field='currency_id', required=True)
```

## 2) Crons idempotentes y válidos (sin python inline en XML)

**Antes** había un cron con comprensión en XML. **Ahora** todos llaman a métodos `_cron_*` del modelo.

```
custom_addons/ai_bridge/data/ir_cron_ml.xml
```

```xml
<odoo>
  <record id="ir_cron_analyze_risk" model="ir.cron">
    <field name="name">Análisis de Riesgos</field>
    <field name="model_id" ref="model_ai_bridge_risk_predictor"/>
    <field name="state">code</field>
    <field name="code">model._cron_analyze_all()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">weeks</field>
    <field name="active">True</field>
  </record>
  <record id="ir_cron_predict_costs" model="ir.cron">
    <field name="name">Pronóstico de Costos</field>
    <field name="model_id" ref="model_ai_bridge_cost_forecaster"/>
    <field name="state">code</field>
    <field name="code">model._cron_predict_all()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">weeks</field>
    <field name="active">True</field>
  </record>
</odoo>
```

```
custom_addons/ai_bridge/models/cost_forecaster.py
```

```python
class CostForecaster(models.Model):
    _name = 'ai_bridge.cost_forecaster'
    # ...
    @api.model
    def _cron_predict_all(self):
        for project in self.env['project.project'].search([]):
            self.predict_costs(project)
```

## 3) Accesos mínimos y record rules por rol

Se agregan **ir.model.access.csv** base por módulo (lectura/escritura según rol) y ejemplo de reglas por proyecto.

```
custom_addons/project_financials/security/ir.model.access.csv
```

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_budget_pm,access_budget_pm,model_project_financials_project_budget,ofitec_security.group_project_manager,1,1,1,0
access_change_pm,access_change_pm,model_project_financials_change_order,ofitec_security.group_project_manager,1,1,1,0
access_budget_admin,access_budget_admin,model_project_financials_project_budget,base.group_system,1,1,1,1
access_change_admin,access_change_admin,model_project_financials_change_order,base.group_system,1,1,1,1
```

**Regla ejemplo (visibilidad por proyecto):**

```
custom_addons/ofitec_security/security/record_rules.xml
```

```xml
<odoo>
  <record id="rule_cashflow_by_project" model="ir.rule">
    <field name="name">Cashflow por proyecto</field>
    <field name="model_id" ref="model_ofitec_cashflow_line"/>
    <field name="groups" eval="[(4, ref('ofitec_security.group_project_manager'))]"/>
    <field name="domain_force">[("project_id","in", user.project_ids.ids)]</field>
  </record>
</odoo>
```

## 4) Idempotencia en bancarización & cashflow

Se agregan claves externas y hashes para evitar duplicados.

```
custom_addons/flow_management/models/bank_models.py
```

```python
class BankLine(models.Model):
    _name = 'flow.bank.line'
    _inherit = ['ofitec.company.currency.mixin']
    external_ref = fields.Char(index=True)
    external_source = fields.Selection([('bci','BCI'),('santander','Santander'),('csv','CSV'),('ofx','OFX')])
    line_hash = fields.Char(index=True)
    _sql_constraints = [
        ('uniq_ext_ref', 'unique(external_ref)', 'Línea bancaria duplicada (external_ref).'),
        ('uniq_line_hash', 'unique(line_hash)', 'Línea bancaria duplicada (hash).'),
    ]

    @api.model
    def compute_hash(self, vals):
        import hashlib, json
        key = json.dumps({k: vals.get(k) for k in ['date','amount','name','bank_id']}, sort_keys=True)
        return hashlib.sha256(key.encode()).hexdigest()
```

```
custom_addons/flow_management/models/cashflow_line.py (fragmento _upsert_line)
```

```python
@api.model
def _upsert_line(self, payload, category):
    ext = payload.get('external_ref')
    if ext:
        rec = self.search([('external_ref','=', ext)], limit=1)
        vals = self._map_payload(payload, category)
        if rec:
            rec.write(vals)
            return rec
        vals['external_ref'] = ext
        return self.create(vals)
    # fallback por hash si no hay external_ref
    vals = self._map_payload(payload, category)
    vals['line_hash'] = self.env['flow.bank.line'].compute_hash(vals)
    rec = self.search([('line_hash','=', vals['line_hash'])], limit=1)
    return rec or self.create(vals)
```

## 5) Revisión de `__init__` / `__manifest__` / `depends`

- Todos los módulos deben importar `models/` en `__init__.py` y declarar `depends` reales (sin sobrecarga).
- `application=False` en addons que no son apps completas.

## 6) Índices y constraints

- Índices en claves de búsqueda (`project_id`, `date_start`, `paid`, `category`).
- Constraints de integridad básica (fechas coherentes, montos ≥ 0).

---

## Estado M0

-

> **Nota:** En la siguiente fase (M1) atacamos Conciliación bancaria (motor de reglas + UI 3 paneles) y conectores BCI/Santander con logs y botón “Sync ahora”.

