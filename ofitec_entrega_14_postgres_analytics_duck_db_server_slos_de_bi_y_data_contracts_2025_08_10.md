# OFITEC – Entrega 14 (Postgres Analytics / DuckDB Server, SLOs de BI y Data Contracts)

> Décima cuarta entrega: elevamos analítica a **nivel producción**. Dos rutas de almacenamiento de marts (**Postgres Analytics** recomendado / **DuckDB Server** opcional), definimos **SLOs de BI** (frescura, latencia, error‑rate, disponibilidad) con **SLIs** instrumentados, y formalizamos **Data Contracts** (esquemas/versionado/pruebas) para endpoints de reporting.

---

## 0) Objetivos

- Soportar **concurrencia y gobernanza** en consultas BI con un motor multiusuario.
- Medir y garantizar **frescura** de datos y **tiempos de respuesta** (SLOs visibles).
- Evitar roturas aguas abajo con **Data Contracts versionados** y **contract tests**.

---

## 1) Ruta A (recomendada): **Postgres Analytics**

### 1.1 Servicio

`infra/docker-compose.prod.yml` (extensión)

```yaml
  pg_analytics:
    image: postgres:15
    environment:
      - POSTGRES_DB=ofitec_analytics
      - POSTGRES_USER=readonly_admin
      - POSTGRES_PASSWORD=${PGAN_PASS}
    volumes:
      - pg_analytics_data:/var/lib/postgresql/data
    networks: [ofitec]
```

`.env`

```bash
PGAN_PASS=cambia-esta-clave
ANALYTICS_DSN=postgresql://readonly_admin:${PGAN_PASS}@pg_analytics:5432/ofitec_analytics
```

### 1.2 DDL base (esquema, roles, RLS opcional por compañía)

`infra/analytics/init.sql`

```sql
CREATE SCHEMA IF NOT EXISTS marts;
CREATE ROLE bi_reader NOINHERIT;
GRANT USAGE ON SCHEMA marts TO bi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts GRANT SELECT ON TABLES TO bi_reader;

-- RLS por compañía (si aplica multiempresa)
CREATE TABLE IF NOT EXISTS marts.dim_company (
  company_id int PRIMARY KEY,
  name text NOT NULL
);
ALTER TABLE marts.dim_company ENABLE ROW LEVEL SECURITY;
CREATE POLICY company_read ON marts.dim_company FOR SELECT TO bi_reader USING (true);
```

> Nota: aplicaremos RLS en **hechos** si necesitas aislamiento por compañía/cliente.

### 1.3 Carga desde el warehouse (DuckDB → Postgres Analytics)

`infra/etl/publish_to_pg.py`

```python
import duckdb, pandas as pd, sqlalchemy, os
PG=os.getenv('ANALYTICS_DSN')
con=duckdb.connect('/warehouse/ofitec.duckdb')
engine=sqlalchemy.create_engine(PG, future=True)

def push(table):
    df=con.execute(f'SELECT * FROM {table}').fetchdf()
    df.to_sql(table.replace('mart_','marts.'), engine, if_exists='replace', index=False)

for t in ('mart_fact_sales','mart_fact_cashflow','mart_ar_aging','mart_ap_aging','mart_kpi_ceo'):
    push(t)
```

Cron (15 min) en el contenedor `etl_runner` para publicar.

### 1.4 Conexión de Metabase / Grafana

- Apuntar Metabase a `pg_analytics` (además del DuckDB local si deseas).
- Ventajas: **concurrencia**, permisos, vistas materializadas, **RLS**.

---

## 2) Ruta B (opcional): **DuckDB Server** ligero

> Si prefieres mantener DuckDB: exponer `ofitec.duckdb` a través de un **servicio fino** que acepte SQL HTTP y controle concurrencia.

`infra/duckdbserver/Dockerfile`

```dockerfile
FROM python:3.11-slim
RUN pip install duckdb==0.10.0 flask==3.0.0
COPY server.py /srv/server.py
CMD ["python","/srv/server.py"]
```

`infra/duckdbserver/server.py`

```python
from flask import Flask, request, jsonify
import duckdb
con = duckdb.connect('/warehouse/ofitec.duckdb', read_only=True)
app = Flask(__name__)
@app.post('/sql')
def sql():
    q = request.json.get('query','')
    if not q.lower().startswith(('select','with')):
        return jsonify({'error':'read-only'}), 400
    df = con.execute(q).fetchdf()
    return jsonify({'rows': df.to_dict('records')})
```

Compose (añadir servicio y montar volumen `warehouse:`). **Advertencia**: es un servidor simple; para alta concurrencia preferir Postgres Analytics.

---

## 3) **SLOs de BI** (objetivos) e **instrumentación** (SLIs)

### 3.1 Definiciones (propuestas iniciales)

- **Frescura** (Freshness): `≤ 20 min` entre hora actual y `max(load_timestamp)` de cada mart crítico.
- **Latencia P95** consultas BI: `≤ 1.5 s` para paneles estándar.
- **Error‑Rate** de consultas: `< 1%` 5xx/errores SQL.
- **Disponibilidad** endpoints BI: `≥ 99.5%` mensual.

### 3.2 Medición de **Frescura**

Agregar columna `load_ts` en cada mart (en ETL) y exportar métrica. `infra/etl/runner.py` (al final de cada materialización)

```python
from datetime import datetime
con.execute("ALTER TABLE mart_fact_cashflow ADD COLUMN IF NOT EXISTS load_ts TIMESTAMP")
con.execute("UPDATE mart_fact_cashflow SET load_ts=?", [datetime.utcnow()])
```

### 3.3 Exportador de SLIs → Prometheus

`infra/metrics/bi_exporter.py`

```python
from flask import Flask, Response
import duckdb, os, psycopg2
MODE=os.getenv('BI_MODE','duckdb')  # duckdb|pg
app=Flask(__name__)

@app.get('/metrics')
def metrics():
    try:
        if MODE=='duckdb':
            con=duckdb.connect('/warehouse/ofitec.duckdb', read_only=True)
            freshness = con.execute("SELECT EXTRACT(EPOCH FROM (now()-max(load_ts))) FROM mart_fact_cashflow").fetchone()[0]
        else:
            con=psycopg2.connect(os.getenv('ANALYTICS_DSN'))
            cur=con.cursor(); cur.execute("SELECT EXTRACT(EPOCH FROM (now()-max(load_ts))) FROM marts.mart_fact_cashflow")
            freshness=cur.fetchone()[0]
        out=f"of_bi_freshness_seconds{{mart='cashflow'}} {freshness}\n"
    except Exception:
        out="of_bi_freshness_seconds{mart='cashflow'} 1e9\n"
    return Response(out, mimetype='text/plain')
```

Compose: añadir `bi_exporter` y scrape en Prometheus; crear alerta `FreshnessAbove20m`.

### 3.4 Latencia y errores

- Grafana/Metabase detrás de Traefik: scrape `request_duration_seconds` y `http_5xx_total` del reverse proxy (o sidecar exporter).
- Reglas adicionales en `prometheus/rules/ofitec.rules.yml`.

---

## 4) **Data Contracts** (esquemas + versionado + tests)

### 4.1 Versionado de API

- Endpoints bajo `/api/v1/...`; cambios breaking → `/api/v2/...`.

### 4.2 Esquemas (JSON Schema / OpenAPI)

`infra/contracts/openapi.yaml` (extracto)

```yaml
openapi: 3.0.3
info:
  title: OFITEC Reporting API
  version: 1.0.0
paths:
  /api/v1/reports/cashflow:
    get:
      summary: Serie de flujo de caja
      parameters:
        - in: query
          name: project_id
          schema: { type: integer }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  required: [date, planned, actual]
                  properties:
                    date: { type: string, format: date }
                    planned: { type: number }
                    actual: { type: number }
```

### 4.3 Validadores de contrato (CI)

`infra/contracts/tests/test_cashflow_contract.py`

```python
import requests, jsonschema
from jsonschema import validate
schema = {
  "type":"array","items":{
    "type":"object","required":["date","planned","actual"],
    "properties":{
      "date":{"type":"string","format":"date"},
      "planned":{"type":"number"},
      "actual":{"type":"number"}
}}}

def test_contract_ok():
  r = requests.get('https://ofitec.tu-dominio.cl/api/v1/reports/cashflow?project_id=1', timeout=5)
  r.raise_for_status()
  validate(r.json(), schema)
```

Integrar en **GitHub Actions** (job de tests de contrato post‑deploy canary).

### 4.4 Vistas materializadas base (Postgres Analytics)

`infra/analytics/marts.sql`

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS marts.mart_fact_cashflow AS
SELECT date, company_id, category, amount_planned, amount_actual, now() AS load_ts
FROM source_cashflow;  -- tabla staging publicada por publish_to_pg.py

CREATE INDEX IF NOT EXISTS idx_cashflow_date ON marts.mart_fact_cashflow(date);
```

`Makefile` target para `REFRESH MATERIALIZED VIEW CONCURRENTLY` (siempre que tenga índice único apropiado).

---

## 5) Seguridad

- **Only‑read** para usuarios BI (`bi_reader`).
- **RLS** cuando haya multiempresa/tenancy.
- **CSP** ya en enforce (Entrega 10/11) protege paneles embebidos.
- **SSO Google** para Metabase/Grafana si se expone públicamente.

---

## 6) QA / Checklist

-

---

## 7) Próxima (Entrega 15)

- **SLOs de usuarios** (tiempo de render por rol/panel) + budgets.
- **dbt** para gestión declarativa de marts.
- **Semantic Layer** (nombres de métricas y dimensiones) + tests.

