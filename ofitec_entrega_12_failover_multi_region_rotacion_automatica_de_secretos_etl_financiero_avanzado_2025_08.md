# OFITEC – Entrega 12 (Failover Multi‑Región, Rotación Automática de Secretos, ETL Financiero Avanzado)

> Duodécima tanda: **alta disponibilidad multi‑región con quorum**, **rotación automática de secretos (Vault)** y **plataforma de analítica financiera** (ETL/Data Vault light + modelos estrella) con dashboards. Todo Community‑safe.

---

## 0) Objetivos

- Tolerar caída total de una región con **conmutación automática** y **RPO ≤ 15 min**.
- Reducir riesgo de credenciales expuestas con **secretos dinámicos/rotados**.
- Unificar datos de OFITEC en un **lago/almacén analítico** para KPIs financieros y de proyectos.

---

## 1) Failover **multi‑región** con quorum

### 1.1 Componentes

```
región-A (primaria):  odoo_blue/green + db_primary + traefik + prom + loki
región-B (secundaria): odoo_blue/green + db_standby + traefik + prom + loki
región-C (quorum): etcd-1 + blackbox + controlador failover (externo)
```

- **DNS** como front door (TTL 30–60s), `A` → VIP región activa.
- **Prometheus** en cada región exporta métricas Odoo/DB.
- **etcd** (3 nodos, 1 por región) para **elección de líder** y **locks**.

### 1.2 Métricas de salud (gates)

- `odoo:p95_5m < 1.2` y `odoo:error_rate_5m < 1%` (definidos en Entrega 10).
- `db:replication_lag_seconds < 900` en standby.

### 1.3 Gestor de failover con quorum

`infra/failover/manager.py`

```python
#!/usr/bin/env python3
import os, time, requests
from etcd3 import Etcd3Client
PROM_A=os.getenv('PROM_A')
PROM_B=os.getenv('PROM_B')
DNS_API=os.getenv('DNS_API')
TARGET_A=os.getenv('IP_A')
TARGET_B=os.getenv('IP_B')
ETCD=os.getenv('ETCD','etcd:2379')
KEY='/ofitec/active'

Q_HEALTH='gate:healthy'
Q_LAG='db:replication_lag_seconds'

def healthy(prom):
    try:
        r=requests.get(prom+'/api/v1/query', params={'query':Q_HEALTH}, timeout=5).json()
        v=float(r['data']['result'][0]['value'][1]) if r['data']['result'] else 0.0
        return v>=1
    except: return False

def lag_ok(prom):
    try:
        r=requests.get(prom+'/api/v1/query', params={'query':Q_LAG}, timeout=5).json()
        v=float(r['data']['result'][0]['value'][1]) if r['data']['result'] else 99999
        return v<900
    except: return False

def set_dns(target_ip):
    # POST al DNS provider (stub); en producción usar Cloudflare/Route53 API
    requests.post(DNS_API,json={'ip':target_ip},timeout=5)

if __name__=='__main__':
    host,port=ETCD.split(':'); etcd=Etcd3Client(host=host, port=int(port))
    while True:
        active = (etcd.get(KEY)[0] or b'A').decode()
        a_ok = healthy(PROM_A)
        b_ok = healthy(PROM_B) and lag_ok(PROM_B)
        # Si activo A falla y B está sano → failover a B
        if active=='A' and not a_ok and b_ok:
            if etcd.lock("ofitec-failover").acquire(timeout=5):
                set_dns(TARGET_B); etcd.put(KEY,'B')
        # Si activo B falla y A sano → volver a A
        if active=='B' and not b_ok and a_ok:
            if etcd.lock("ofitec-failover").acquire(timeout=5):
                set_dns(TARGET_A); etcd.put(KEY,'A')
        time.sleep(10)
```

> Evita *split‑brain* gracias al **lock distribuido** en etcd. El cambio es por **DNS** para ambas regiones.

### 1.4 Postgres cross‑región

- **WAL archiving** a bucket multi‑región (Entrega 10). Standby en B aplica WAL.
- Opción: **logical replication** para lecturas analíticas en B sin impactar A.
- RPO objetivo **≤ 15 min**.

---

## 2) **Rotación automática de secretos** (Vault)

### 2.1 Secretos dinámicos de Postgres

- Habilitar **Database Secrets Engine** en Vault (rol `odoo-app` con `ttl=1h`, `max_ttl=24h`).
- Odoo usará un **usuario CN** (conectado vía proxy) o se refrescará por **deploy canary**.

`infra/secrets/postgres-role.sql` (plantilla)

```sql
CREATE ROLE "{{name}}" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';
GRANT CONNECT ON DATABASE ofitec_prod TO "{{name}}";
GRANT USAGE ON SCHEMA public TO "{{name}}";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{{name}}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{{name}}";
```

### 2.2 Rotador (cron) → canary → switch

`infra/secrets/rotate_and_deploy.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
export VAULT_ADDR VAULT_TOKEN
# 1) Obtener creds dinámicas
CREDS=$(curl -sH "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/database/creds/odoo-app)
USER=$(echo $CREDS | jq -r .data.username)
PASS=$(echo $CREDS | jq -r .data.password)
# 2) Render .env GREEN y despliegue canary
cp infra/.env infra/.env.bak
awk -v u="$USER" -v p="$PASS" 'BEGIN{FS=OFS="="} /^POSTGRES_USER=/{$2=u} /^POSTGRES_PASSWORD=/{
$2=p} {print}' infra/.env > infra/.env.new && mv infra/.env.new infra/.env
make -C infra canary
# 3) Si health OK (gates 15m), switch
python3 infra/autoscaler/switcher.py --one-shot || true
# 4) Rotar color frío (opcional) y limpiar
```

### 2.3 AWS STS (credenciales efímeras)

- Para **restic**/S3: usar **role** con `duration=1h`; el rotador obtiene **session tokens** y actualiza `.env` del contenedor `restic`.

---

## 3) **ETL financiero** (Data Vault light + modelos estrella)

### 3.1 Arquitectura de datos

```
/warehouse
├─ raw/           # dumps Odoo (CSV/Parquet) por módulo
├─ stage/         # limpieza tipificada
├─ vault/         # hubs, links, satellites (historia)
└─ marts/         # modelos estrella (BI): ventas, flujo, presupuestos, WIP
```

### 3.2 Extracción (Odoo → RAW)

- Endpoints `/of/export/*` devuelven CSV/JSON **incremental** por `write_date`.
- Programación: `etl_runner` cada 15 min.

### 3.3 Transformación – Python + DuckDB

`infra/etl/runner.py`

```python
#!/usr/bin/env python3
import duckdb, pandas as pd, os, glob
DB='/warehouse/ofitec.duckdb'
con=duckdb.connect(DB)
# 1) RAW → STAGE (tipificación básica)
for path in glob.glob('/warehouse/raw/*.csv'):
    tbl=os.path.basename(path).split('.')[0]
    df=pd.read_csv(path)
    con.execute(f'CREATE TABLE IF NOT EXISTS stage_{tbl} AS SELECT * FROM df')
    con.execute(f'DELETE FROM stage_{tbl} WHERE true')
    con.register('df', df); con.execute(f'INSERT INTO stage_{tbl} SELECT * FROM df')
# 2) STAGE → VAULT (hubs/links/sats ejemplo)
con.execute('''
CREATE TABLE IF NOT EXISTS vault_h_project AS SELECT DISTINCT project_id AS hk_project, any_value(project_name) AS name FROM stage_project;''')
con.execute('''
CREATE TABLE IF NOT EXISTS vault_h_partner AS SELECT DISTINCT partner_id AS hk_partner, any_value(partner_name) AS name FROM stage_partner;''')
con.execute('''
CREATE TABLE IF NOT EXISTS vault_l_project_invoice AS
SELECT DISTINCT project_id AS hk_project, invoice_id AS hk_invoice FROM stage_invoice;''')
con.execute('''
CREATE TABLE IF NOT EXISTS vault_s_invoice AS
SELECT invoice_id AS hk_invoice, date, amount_total, amount_tax, state FROM stage_invoice;''')
# 3) MARTS (estrella: ventas)
con.execute('''
CREATE TABLE IF NOT EXISTS mart_fact_sales AS
SELECT i.date, p.hk_project, s.amount_total, s.amount_tax
FROM vault_l_project_invoice i
JOIN vault_s_invoice s USING(hk_invoice)
LEFT JOIN vault_h_project p USING(hk_project);
''')
con.close()
```

### 3.4 Marts de **Flujo de Caja** y **WIP**

- `mart_fact_cashflow`: integra `of.cashflow.line` (planned/actual) por proyecto, categoría y fecha.
- `mart_fact_wip`: progreso físico vs valor ganado (EVM), integra avance de `site_management` y costos.

### 3.5 Validaciones ligeras (calidad de datos)

`infra/etl/checks.yml`

```yaml
checks:
  - table: mart_fact_sales
    tests:
      - not_null: [date, hk_project]
      - positive: [amount_total]
  - table: mart_fact_cashflow
    tests:
      - not_null: [date]
      - enum: {column: status, values: [planned, actual]}
```

`infra/etl/validate.py`

```python
import yaml, duckdb
conf=yaml.safe_load(open('infra/etl/checks.yml'))
con=duckdb.connect('/warehouse/ofitec.duckdb')
for c in conf['checks']:
    t=c['table']
    for col in c.get('tests',{}).get('not_null',[]):
        assert con.execute(f"SELECT count(*) FROM {t} WHERE {col} IS NULL").fetchone()[0]==0
```

### 3.6 Dashboards

- **Grafana/Metabase** conectados a DuckDB (via DuckDB SQL over server) o export a **Postgres analytics** (replicar `marts/*`).
- KPIs: **Margen Bruto**, **Días de Caja**, **Backlog** y **WIP** por proyecto.

---

## 4) Orquestación y Compose

`infra/docker-compose.prod.yml` (extensión)

```yaml
  etcd:
    image: quay.io/coreos/etcd:v3.5
    command: ["etcd","--name=etcd1","--advertise-client-urls=http://0.0.0.0:2379","--listen-client-urls=http://0.0.0.0:2379"]
    networks: [ofitec]

  failover_mgr:
    image: python:3.11-slim
    env_file: .env
    volumes:
      - ./failover:/opt/failover
    command: ["python","/opt/failover/manager.py"]
    networks: [ofitec]

  etl_runner:
    image: python:3.11-slim
    volumes:
      - ./etl:/opt/etl
      - warehouse:/warehouse
    command: ["bash","-lc","cron -f"]
    env_file: .env
```

Volumen `warehouse:` persistente para el lago analítico.

---

## 5) Seguridad y cumplimiento

- **Principio SSOT**: fuentes operacionales siguen en Odoo; el **warehouse** es **read‑only** aguas abajo.
- **Mascarado**: columnas sensibles (RUT, correo, teléfono) tokenizadas en `stage_*` si se exporta a BI externo.
- **Límites**: accesos a DuckDB/Postgres analytics con **read‑only** y **SSO** (Google) si se publica.

---

## 6) QA / Checklist

-

---

## 7) Próxima (Entrega 13)

- **Quorum multi‑región activo/activo** (lecturas en B, escrituras en A).
- **Catálogo de datos** (línea base de metadatos + linaje).
- **Paquete de dashboards** (Metabase provisionado + colecciones).

