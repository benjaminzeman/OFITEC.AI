# OFITEC – Entrega 13 (Activo/Activo Lecturas, Catálogo & Linaje de Datos, Dashboards Pack)

> Décimo tercera entrega enfocada en **escalabilidad de lecturas** (activo/activo), **gobierno de datos** (catálogo & linaje) y **paquete de dashboards** listo para usar. Todo Community‑safe.

---

## 0) Objetivos

- Desacoplar lecturas pesadas del primario: **replica‑first** para consultas analíticas y APIs de reporting.
- **Catálogo & linaje** mínimo viable para trazabilidad de KPIs.
- **Dashboards** (C‑level / Finanzas / Proyectos) provisionados de forma automática.

---

## 1) Activo/Activo de **lecturas** (replicas + routing seguro)

### 1.1 Enfoque arquitectónico

- **Escrituras** (transaccional Odoo) → **primario** (A).
- **Lecturas** de reporting (GraphQL/CEO Dash/Series) → **réplica**(s) (B), coherencia eventual (≤ 1–5 min).
- Odoo no soporta routing automático de statements; resolvemos con **conexiones dedicadas** en los **controladores/servicios** de lectura.

### 1.2 Variables de entorno

`.env`

```bash
READ_REPLICA_DSN=postgresql://ro_user:ro_pass@db-replica:5432/ofitec_prod
REPLICA_MAX_LAG_S=900
```

### 1.3 Helper de conexión **read‑only**

`infra/app/of_db_router.py`

```python
import psycopg2, os, time
from contextlib import contextmanager

REPLICA_DSN = os.getenv('READ_REPLICA_DSN')
MAX_LAG = int(os.getenv('REPLICA_MAX_LAG_S','900'))

@contextmanager
def replica_cursor():
    if not REPLICA_DSN:
        raise RuntimeError('Replica DSN not configured')
    conn = psycopg2.connect(REPLICA_DSN)
    conn.set_session(readonly=True, autocommit=True)
    # fast health: check replica lag
    with conn.cursor() as c:
        try:
            c.execute("SELECT EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())::int")
            lag = c.fetchone()[0] or 0
            if lag > MAX_LAG:
                raise RuntimeError(f'Replica lag {lag}s > {MAX_LAG}s')
        except Exception:
            conn.close(); raise
    try:
        with conn.cursor() as cur:
            yield cur
    finally:
        conn.close()
```

### 1.4 Uso en controladores de **series/GraphQL**

`custom_addons/of_ceo_dashboard/controllers/kpi_series.py` (extracto)

```python
from odoo import http
from odoo.http import request
from infra.app.of_db_router import replica_cursor

class CeoKpiSeries(http.Controller):
    @http.route('/of/ceo/aging_series_ro', type='json', auth='user')
    def aging_ro(self, days=180):
        # Consulta directa a tablas agregadas desde réplica
        with replica_cursor() as cur:
            cur.execute('''
                SELECT date, ar_b0_30, ar_b31_60, ar_b61_90, ar_b90p,
                       ap_b0_30, ap_b31_60, ap_b61_90, ap_b90p, supply_lt
                FROM of_ceo_kpi_daily
                WHERE date >= now()::date - INTERVAL '%s days'
                ORDER BY date ASC
            ''', (days,))
            rows = cur.fetchall()
        return [
            { 'date': str(r[0]), 'ar':[r[1],r[2],r[3],r[4]], 'ap':[r[5],r[6],r[7],r[8]], 'supply_lt': r[9] }
            for r in rows
        ]
```

> **Nota:** protegemos integridad: si la réplica está atrasada más allá del umbral, el helper **falla** y el controlador puede hacer *fallback* al primario (opcional).

### 1.5 Fallback seguro (opcional)

```python
try:
    data = self.aging_ro(days)
except Exception:
    data = self.aging(days)  # endpoint original (primario)
```

### 1.6 Pool de réplicas (round‑robin)

`infra/app/of_db_router.py` (extensión)

```python
REPLICA_DSN = os.getenv('READ_REPLICA_DSN','').split(',')  # permite lista
_rr = 0

def _pick():
    global _rr
    if not REPLICA_DSN: raise RuntimeError('Replica DSN list empty')
    dsn = REPLICA_DSN[_rr % len(REPLICA_DSN)]; _rr += 1
    return dsn
```

---

## 2) **Catálogo & Linaje** (OpenLineage + Marquez)

### 2.1 Compose (servicios)

`infra/docker-compose.prod.yml` (añadir)

```yaml
  marquez:
    image: marquezproject/marquez:latest
    environment:
      - MARQUEZ_PORT=5000
    ports: ["5001:5000"]
    networks: [ofitec]
```

### 2.2 Emisión de eventos desde el ETL

`infra/etl/lineage.py`

```python
import os, requests, time
URL=os.getenv('MARQUEZ_URL','http://marquez:5000')
NS='ofitec'

def emit_job_run(job, inputs, outputs, status='COMPLETE'):
    payload={
      'job': {'namespace':NS,'name':job},
      'run': {'id': str(int(time.time()))},
      'inputs': [{'namespace':NS,'name':i} for i in inputs],
      'outputs': [{'namespace':NS,'name':o} for o in outputs],
      'eventType': status
    }
    requests.post(f'{URL}/api/v1/lineage', json=payload, timeout=5)
```

Uso en `runner.py` (Entrega 12):

```python
from lineage import emit_job_run
emit_job_run('raw_to_stage', inputs=['raw_project','raw_invoice'], outputs=['stage_project','stage_invoice'])
emit_job_run('stage_to_vault', inputs=['stage_*'], outputs=['vault_*'])
emit_job_run('vault_to_marts', inputs=['vault_*'], outputs=['mart_fact_sales','mart_fact_cashflow'])
```

### 2.3 Catálogo mínimo de datasets

`warehouse/catalog.yml`

```yaml
- name: mart_fact_cashflow
  description: "Flujo de caja (planned/actual) por fecha y proyecto"
  owner: finanzas@ofitec.cl
  pii: false
- name: mart_fact_wip
  description: "Valor ganado (EVM) por proyecto y período"
  owner: pmo@ofitec.cl
  pii: false
```

---

## 3) **Dashboards Pack** (Metabase provisioning)

### 3.1 Servicio Metabase

`infra/docker-compose.prod.yml` (añadir)

```yaml
  metabase:
    image: metabase/metabase:latest
    ports: ["3001:3000"]
    environment:
      - MB_DB_FILE=/metabase.db
    volumes:
      - metabase_data:/metabase.db
    networks: [ofitec]
```

### 3.2 Provisioning Script

`infra/bi/provision_metabase.py`

```python
import os, requests, time
MB=os.getenv('MB_URL','http://metabase:3000')
USER=os.getenv('MB_USER','admin@ofitec.cl')
PASS=os.getenv('MB_PASS','changeme')
DB_URI=os.getenv('MB_DUCKDB_URI','/warehouse/ofitec.duckdb')

s=requests.Session()
# 1) Login
r=s.post(f'{MB}/api/session', json={'username':USER,'password':PASS}).json()
# 2) Add DuckDB (or Postgres analytics)
s.post(f'{MB}/api/database', json={
  'name':'OFITEC Warehouse', 'engine':'duckdb', 'details':{'db':DB_URI}
})
# 3) Create Collection
col=s.post(f'{MB}/api/collection', json={'name':'OFITEC KPIs'}).json()
col_id=col['id']
# 4) Cards (ejemplos)
def card(name, dataset, query):
    s.post(f'{MB}/api/card', json={
      'name': name, 'dataset_query': {'type':'native','native':{'query':query}}, 'display':'line', 'collection_id': col_id
    })
card('Días de Caja', 'mart_fact_cashflow', """
select date, sum(amount_actual) over (order by date) as saldo
from mart_fact_cashflow order by date
""")
card('AR Aging Total', 'mart_ar_aging', "select * from mart_ar_aging order by date")
```

### 3.3 Modelos de BI sugeridos

- `mart_ar_aging`: buckets AR por fecha.
- `mart_ap_aging`: buckets AP por fecha.
- `mart_kpi_ceo`: unión de KPIs claves (cash days, backlog, IVA due/diferido, lead‑time abastecimiento).

---

## 4) Seguridad y gobernanza

- **Read‑only users** para réplicas y warehouse; sin credenciales compartidas.
- **Enmascaramiento** (column‑level) si se publica BI a terceros.
- **Lineage** visible: de KPI → mart → vault → stage → raw → Odoo, para auditoría.

---

## 5) QA / Checklist

-

---

## 6) Próxima (Entrega 14)

- **Mode Server** para DuckDB (conexiones concurrentes) o migrar marts a **Postgres analytics**.
- **SLOs** de BI (tiempos de actualización y frescura observables).
- **Data Contracts** (esquemas versionados para endpoints de reporting).

