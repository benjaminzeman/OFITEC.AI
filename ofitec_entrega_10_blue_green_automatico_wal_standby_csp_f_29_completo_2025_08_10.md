# OFITEC – Entrega 10 (Blue/Green automático, WAL + Standby, CSP, F29 completo)

> Décima tanda: **automatización Blue/Green** con *health gates* (latencia/errores), **Postgres WAL archiving + Standby** (RPO≈15 min, RTO≈10–30 min), **CSP/seguridad avanzada** en Traefik y **F29 completo** con mapeo por casillas, validadores y fixtures. Community‑safe, sin Enterprise.

---

## 0) Contenido y ubicación

```
/infra
├─ docker-compose.prod.yml              # actualizado (blackbox + node-exporter opc.)
├─ traefik/dynamic/security.yml         # <<< CSP/headers estrictos
├─ autoscaler/
│  ├─ autoscaler.py
│  └─ switcher.py                       # <<< decide canary→switch automático
├─ prometheus/rules/ofitec.rules.yml    # extendido (gates de deploy)
├─ postgres/
│  ├─ primary/postgresql.conf           # <<< WAL archiving
│  ├─ primary/pg_hba.conf
│  ├─ standby/postgresql.conf           # <<< read only
│  ├─ standby/recovery.conf             # (v12+: standby.signal + primary_conninfo)
│  └─ scripts/{create_slot.sh, promote.sh}
└─ runbooks/
   ├─ dr_plan.md                        # actualizado (WAL + standby)
   └─ playbooks/deploy_bluegreen.md

/custom_addons
└─ of_sii_cl/
   ├─ data/f29_mapping.yml              # ampliado / casillas reales
   ├─ models/{f29.py,f29_map.py}       # validadores y sumarias
   ├─ tests/test_f29_mapping.py         # <<< fixtures & asserts
   └─ wizards/{f29_export_wizard.py,f29_validate_wizard.py}
```

---

## 1) Blue/Green **automático** (health‑gated)

### 1.1 Reglas de *gates* (Prometheus)

`infra/prometheus/rules/ofitec.rules.yml` (extensión)

```yaml
groups:
- name: deploy-gates
  rules:
  - record: odoo:p95_5m
    expr: histogram_quantile(0.95, sum(rate(odoo_request_latency_seconds_bucket[5m])) by (le))
  - record: odoo:error_rate_5m
    expr: sum(rate(odoo_http_5xx_total[5m])) / sum(rate(odoo_http_requests_total[5m]))
  - record: gate:healthy
    expr: (odoo:p95_5m < 1.2) and (odoo:error_rate_5m < 0.01)
```

### 1.2 Switcher automático

`infra/autoscaler/switcher.py`

```python
#!/usr/bin/env python3
import os, time, requests, subprocess
PROM=os.getenv('PROM_URL','http://prometheus:9090')
QUERY='gate:healthy'
COLOR_ACTIVE=os.getenv('ACTIVE','blue')
COLOR_CANARY='green' if COLOR_ACTIVE=='blue' else 'blue'
SUSTAIN_S=900  # 15 min saludable antes de switch

ok_since=None
while True:
    try:
        r=requests.get(PROM+'/api/v1/query', params={'query':QUERY}, timeout=5).json()
        val=float(r['data']['result'][0]['value'][1]) if r['data']['result'] else 0.0
        if val>=1:
            if ok_since is None: ok_since=time.time()
            if time.time()-ok_since>=SUSTAIN_S:
                # Switch definitivo (100% al canary)
                subprocess.run(['make','-C','infra','switch'], check=True)
                # rotar roles
                COLOR_ACTIVE, COLOR_CANARY = COLOR_CANARY, COLOR_ACTIVE
                ok_since=None
        else:
            ok_since=None
    except Exception as e:
        print('switcher:', e)
    time.sleep(30)
```

> Flujo: CI despliega color **frío** → hace **canary** → si las métricas cumplen gates por **15 min**, `switcher.py` hace `make switch`. Si fallan, no hay switch.

### 1.3 Playbook

`runbooks/playbooks/deploy_bluegreen.md`

```
1) Pipeline CI → green (10%)
2) Ver Grafana (p95, error_rate)
3) switcher.py hará switch automático si cumple gates 15m
4) Si falla: rollback (switch back, drenar), abrir issue con logs de Loki
```

---

## 2) Postgres **WAL archiving + Standby**

### 2.1 Primary

`infra/postgres/primary/postgresql.conf`

```conf
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://ofitec-pg-wal/%f'
max_wal_size = '2GB'
wal_keep_size = '512MB'
hot_standby = on
```

`infra/postgres/primary/pg_hba.conf`

```
# replica user
host replication replica 0.0.0.0/0 md5
```

`infra/postgres/scripts/create_slot.sh`

```bash
psql -U $POSTGRES_USER -c "SELECT * FROM pg_create_physical_replication_slot('ofitec_slot');"
```

### 2.2 Standby

`infra/postgres/standby/postgresql.conf`

```conf
hot_standby = on
primary_conninfo = 'host=PRIMARY_IP port=5432 user=replica password=REPL_PASS application_name=ofitec_standby'
primary_slot_name = 'ofitec_slot'
restore_command = 'aws s3 cp s3://ofitec-pg-wal/%f %p'
```

Crear `standby.signal` en data dir del standby.

`infra/postgres/scripts/promote.sh`

```bash
pg_ctl -D /var/lib/postgresql/data promote
```

### 2.3 DR actualizado (extracto de `runbooks/dr_plan.md`)

```
RPO objetivo: 15 min (WAL a S3)
RTO objetivo: 10–30 min (promote standby + switch DNS)
Pasos:
1) Verificar último WAL aplicado en standby
2) Ejecutar promote.sh
3) Cambiar DSN en Odoo (.env → db_host=standby)
4) Habilitar tráfico en Traefik
5) Post-mortem y back‑sync cuando primary vuelva
```

> Opcional: `archive_timeout=60s` para asegurar flush de WAL cada minuto.

---

## 3) **CSP y seguridad avanzada** (Traefik)

`infra/traefik/dynamic/security.yml`

```yaml
http:
  middlewares:
    strict-security:
      headers:
        contentSecurityPolicy: >-
          default-src 'self'; img-src 'self' data: blob:; media-src 'self' data: blob:;
          style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-eval';
          connect-src 'self' https: wss:; font-src 'self' data:; frame-ancestors 'none';
          base-uri 'self'; form-action 'self'; object-src 'none';
        referrerPolicy: no-referrer
        permissionsPolicy: >-
          geolocation=(), microphone=(), camera=(), payment=(), interest-cohort=()
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        browserXssFilter: true
        contentTypeNosniff: true
        frameDeny: true
```

Aplicar el middleware al router Odoo con label:

```
traefik.http.routers.odoo.middlewares=sec-headers@file,strict-security@file
```

> Ajustar `script-src` si cargas librerías externas; idealmente empacarlas localmente.

---

## 4) **F29 completo** – mapeo, validadores y fixtures

### 4.1 Mapeo ampliado (`data/f29_mapping.yml` – ejemplo)

```yaml
- name: IVA Débito 19% (casilla 29)
  tax_xmlid: account.tax_iva_19
  casilla: '29'
  tipo: debito
- name: IVA Débito ítem exento (casilla 30)
  tax_xmlid: account.tax_exento
  casilla: '30'
  tipo: debito
- name: IVA Crédito 19% (casilla 49)
  tax_xmlid: account.tax_iva_19_compra
  casilla: '49'
  tipo: credito
- name: Retenciones (honorarios) (casilla 60)
  tax_xmlid: account.tax_ret_honor
  casilla: '60'
  tipo: credito
```

### 4.2 Validadores (extracto `models/f29.py`)

```python
@api.constrains('period','status')
def _check_closed(self):
    if self.status in ('sent','paid'):
        raise ValidationError('Periodo cerrado: no puede recalcular o modificar F29 enviado/pagado.')

def validate_mapping(self):
    # advierte impuestos en facturas del periodo sin casilla
    missing=set()
    for mv in self.env['account.move'].search([('invoice_date','like', self.period+'%'),('state','=','posted')]):
        for l in mv.invoice_line_ids:
            for t in l.tax_ids:
                if not self.env['of.sii.f29.map'].search([('tax_id','=',t.id)], limit=1):
                    missing.add(t.name)
    if missing:
        self.message_post(body=f"Impuestos sin casilla: {', '.join(sorted(missing))}")
```

### 4.3 Wizard “Validar & Exportar”

- **Validar**: ejecuta `validate_mapping()`, chequea sumatorias por casilla y totales débito/crédito.
- **Exportar**: CSV/JSON/XML como en Entrega 8.

### 4.4 Tests (`tests/test_f29_mapping.py` – extracto)

```python
def test_all_period_taxes_are_mapped(env):
    f = env['of.sii.f29'].create({'period':'2025-08'})
    f.action_compute()
    # Debe no registrar impuestos faltantes en environments con mapping completo
    assert 'Impuestos sin casilla' not in ''.join(f.message_ids.mapped('body'))
```

---

## 5) QA & Checklist

-

---

## 6) Siguientes (Entrega 11)

- **Failover automático** (VIP/Keepalived o DNS API) cuando primary caiga.
- **Report‑Only CSP** → Enforce gradual + colector de `csp-report`.
- **Repositorio de *****secrets*** (Vault) y rotación automática.
- **SII**: integración futura con servicio electrónico si habilitan API.

