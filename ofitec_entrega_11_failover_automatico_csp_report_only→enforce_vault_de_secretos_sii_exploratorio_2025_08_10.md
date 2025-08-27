# OFITEC – Entrega 11 (Failover Automático, CSP Report‑Only→Enforce, Vault de Secretos, SII Exploratorio)

> Objetivo: **cero‑downtime resiliente**: **failover automático** (VRRP o DNS), **CSP en modo Report‑Only → Enforce** con colector, **gestión de secretos con Vault** (rotación) y **conectores SII** en modo exploratorio (contratos/formatos, sin depender de APIs no oficiales). Todo Community‑safe.

---

## 0) Paquetes y estructura

```
/infra
├─ failover/
│  ├─ keepalived/keepalived.conf           # VRRP (si hay L2 compartida)
│  ├─ health.sh                             # chequeo de salud Odoo
│  └─ dns_failover.py                       # alternativa con DNS (Cloudflare/Route53)
├─ autoscaler/switcher.py                   # (Entrega 10) – sin cambios
├─ traefik/dynamic/{security.yml, security_report_only.yml}
├─ secrets/
│  ├─ policy.hcl                            # política Vault
│  ├─ render_env.sh                         # plantillas .env desde Vault
│  └─ rotation.md                           # procedimiento de rotación
└─ runbooks/
   ├─ playbooks/failover_automatico.md
   └─ dr_plan.md                            # actualizado

/custom_addons
└─ of_security_csp/
   ├─ __manifest__.py
   ├─ controllers/csp.py                    # endpoint colector
   ├─ models/csp.py                         # almacenamiento de reportes
   └─ views/csp_views.xml

/custom_addons/of_sii_cl/
├─ models/
│  ├─ f29.py                                # + validadores y estados
│  └─ connector.py                          # interfaz de conectores SII
├─ services/
│  ├─ sii_stub.py                           # stub (manual/upload)
│  └─ sii_partner_adapter.py                # interfaz para proveedor/partner si aplica
└─ views/connector_views.xml
```

---

## 1) Failover automático

### 1.1 Opción A – **VRRP (Keepalived)** con VIP

**Requisito**: los dos servidores (primary/standby) comparten la misma red L2.

`infra/failover/keepalived/keepalived.conf` (en **ambos**; cambia `state` y `priority`)

```conf
vrrp_script chk_odoo {
  script "/opt/health.sh"
  interval 5
  fall 2
  rise 2
}

vrrp_instance VI_OFITEC {
  interface eth0
  virtual_router_id 51
  priority 150           # primary:150, standby:100
  advert_int 1
  authentication {
    auth_type PASS
    auth_pass supersecret
  }
  virtual_ipaddress {
    10.0.0.50/24         # VIP que usa Traefik (80/443)
  }
  track_script {
    chk_odoo
  }
}
```

`infra/failover/health.sh`

```bash
#!/usr/bin/env bash
# Devuelve 0 (OK) si Odoo responde rápido y DB viva
set -e
curl -sk --max-time 2 https://OFITEC_HOST/web/login >/dev/null || exit 1
pg_isready -h 127.0.0.1 -p 5432 >/dev/null || exit 1
exit 0
```

**Notas**

- Traefik escucha en el **VIP** (10.0.0.50). Al caer el primario, keepalived **mueve** el VIP al standby.
- Añadir `systemd` unit para keepalived y desplegar con Ansible o manual (instalar en host, no en contenedor para ARP/VRRP estable).

### 1.2 Opción B – **DNS Failover** (si no hay L2 compartida)

`infra/failover/dns_failover.py` (Cloudflare como ejemplo; Route53 similar)

```python
#!/usr/bin/env python3
import os, time, requests
ZONE=os.getenv('CF_ZONE')
REC=os.getenv('CF_RECORD')
TOKEN=os.getenv('CF_TOKEN')
TARGET=os.getenv('FAILOVER_IP')
PROM=os.getenv('PROM_URL','http://prometheus:9090')
QUERY='gate:healthy'  # de Entrega 10

HEAD={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

def cf_get_record():
    z = requests.get(f'https://api.cloudflare.com/client/v4/zones?name={ZONE}', headers=HEAD).json()['result'][0]['id']
    r = requests.get(f'https://api.cloudflare.com/client/v4/zones/{z}/dns_records?name={REC}', headers=HEAD).json()['result'][0]
    return z, r['id'], r

def cf_update_ip(ip):
    z, rid, r = cf_get_record()
    r['content'] = ip
    requests.put(f'https://api.cloudflare.com/client/v4/zones/{z}/dns_records/{rid}', headers=HEAD, json=r)

ok=False; since=0
while True:
    try:
        val = requests.get(PROM+'/api/v1/query', params={'query':QUERY}, timeout=5).json()['data']['result']
        healthy = bool(val and float(val[0]['value'][1])>=1)
        if not healthy:
            # activar standby
            cf_update_ip(TARGET)
        time.sleep(15)
    except Exception as e:
        time.sleep(15)
```

**Notas**

- Requiere **TTL bajo** (30–60s) en el registro A de `ODOO_HOST`.
- El script se puede ejecutar en un **watchdog** externo o en ambos nodos con *split‑brain guard* (solo standby actualiza si health primario cae).

---

## 2) CSP – Report‑Only → Enforce con colector

### 2.1 Middleware Traefik Report‑Only

`infra/traefik/dynamic/security_report_only.yml`

```yaml
http:
  middlewares:
    csp-report-only:
      headers:
        contentSecurityPolicyReportOnly: >-
          default-src 'self'; img-src 'self' data: blob:; media-src 'self' data: blob:;
          style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-eval';
          connect-src 'self' https: wss:; font-src 'self' data:; frame-ancestors 'none';
          base-uri 'self'; form-action 'self'; object-src 'none'; report-to csp-endpoint; report-uri /csp/report
        reportTo:
          - group: csp-endpoint
            max_age: 10886400
            endpoints:
              - url: https://${ODOO_HOST}/csp/report
```

Aplicar **report‑only** primero al router Odoo y mantener `strict-security@file` en paralelo.

### 2.2 Módulo `of_security_csp` – Colector de reportes

`__manifest__.py`

```python
{
  "name": "OFITEC – CSP Reports",
  "version": "16.0.1.0.0",
  "depends": ["base","web"],
  "data": ["views/csp_views.xml"],
  "license": "LGPL-3"
}
```

`controllers/csp.py`

```python
from odoo import http
from odoo.http import request
import json

class CSP(http.Controller):
    @http.route('/csp/report', type='json', auth='public', csrf=False)
    def report(self):
        payload = request.get_json_data() or {}
        request.env['of.security.csp.report'].sudo().create({'payload': json.dumps(payload)})
        return {"status":"ok"}
```

`models/csp.py`

```python
from odoo import models, fields

class CspReport(models.Model):
    _name = 'of.security.csp.report'
    _description = 'CSP Violation Report'
    create_date = fields.Datetime()
    payload = fields.Text()
```

**Paso a Enforce**

- Analizar reportes 7–14 días, listar orígenes requeridos y **blanquear** explícitamente.
- Cambiar middleware a `strict-security@file` (Entrega 10) como **único** CSP y retirar `report-only`.

---

## 3) Vault de secretos (KV v2)

### 3.1 Política mínima (`infra/secrets/policy.hcl`)

```hcl
path "kv/data/ofitec/*" {
  capabilities = ["read"]
}
```

### 3.2 Render de `.env` desde Vault (`infra/secrets/render_env.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${VAULT_ADDR:?}"
: "${VAULT_TOKEN:?}"
SECRETS=${SECRETS_PATH:-kv/data/ofitec/prod}
JSON=$(curl -sH "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/$SECRETS)
# extrae .data.data
python3 - "$JSON" <<'PY'
import sys, json
j=json.loads(sys.argv[1])
d=j.get('data',{}).get('data',{})
for k,v in d.items():
    print(f"{k}={v}")
PY
```

**Uso**

```
VAULT_ADDR=https://vault.tu-dom.cl \
VAULT_TOKEN=s.xxxx \
SECRETS_PATH=kv/data/ofitec/prod \
infra/secrets/render_env.sh > infra/.env
```

### 3.3 Rotación (extracto `infra/secrets/rotation.md`)

```
Mensual:
1) Generar nueva clave DB y RESTIC_PASSWORD en Vault (versionado KV v2)
2) Aplicar cambio en standby: render_env.sh + canary a green
3) switch → green activo
4) Rotar en blue (ahora frío) y alinear
5) Registrar en runbook; revocar tokens antiguos
```

---

## 4) SII – conectores exploratorios

### 4.1 Interfaz de conector (`of_sii_cl/models/connector.py`)

```python
from odoo import models, fields

class SiiConnector(models.Model):
    _name = 'of.sii.connector'
    _description = 'Conector SII (exploratorio)'

    name = fields.Char(required=True)
    kind = fields.Selection([('manual','Manual/Archivo'),('partner','Partner/Proveedor')], default='manual')
    active = fields.Boolean(default=True)
    notes = fields.Text()

    def action_sync(self):
        # Hook para traer estado de declaraciones o subir archivos,
        # la implementación concreta va en services/*
        return True
```

### 4.2 Stub manual (`services/sii_stub.py`)

```python
class SIIStub:
    def upload_file(self, f29):
        # Genera archivo local (CSV/XML) y guía al usuario para subirlo en el portal SII
        return {'status':'local_exported'}
```

### 4.3 Adaptador a partner (`services/sii_partner_adapter.py`)

```python
class SIIPartnerAdapter:
    def __init__(self, base_url, api_key):
        self.base_url = base_url; self.api_key = api_key
    def send_f29(self, payload):
        # POST al partner autorizado (si se contrata)
        return {"status":"sent","id":"EXT-123"}
```

### 4.4 Vistas de conectores (`views/connector_views.xml`)

```xml
<odoo>
  <record id="view_sii_connector_tree" model="ir.ui.view">
    <field name="name">of.sii.connector.tree</field>
    <field name="model">of.sii.connector</field>
    <field name="arch" type="xml">
      <tree>
        <field name="name"/>
        <field name="kind"/>
        <field name="active"/>
      </tree>
    </field>
  </record>
  <record id="view_sii_connector_form" model="ir.ui.view">
    <field name="name">of.sii.connector.form</field>
    <field name="model">of.sii.connector</field>
    <field name="arch" type="xml">
      <form>
        <sheet>
          <group>
            <field name="name"/>
            <field name="kind"/>
            <field name="active"/>
            <field name="notes"/>
          </group>
          <footer>
            <button name="action_sync" type="object" string="Sincronizar" class="btn-primary"/>
          </footer>
        </sheet>
      </form>
    </field>
  </record>
  <menuitem id="menu_sii_connectors" name="Conectores" parent="of_sii_cl.menu_sii_root" action="action_sii_connector"/>
  <record id="action_sii_connector" model="ir.actions.act_window">
    <field name="name">Conectores SII</field>
    <field name="res_model">of.sii.connector</field>
    <field name="view_mode">tree,form</field>
  </record>
</odoo>
```

**Estrategia**

- **Hoy**: exportación local (CSV/XML) y registro en Flujo.
- **Mañana**: integrar un **partner autorizado** (si el cliente lo requiere) vía `SIIPartnerAdapter`.

---

## 5) Runbooks actualizados

`runbooks/playbooks/failover_automatico.md`

```
1) VRRP: validar VIP en standby tras caída (arping VIP, ping, /web/login OK)
2) DNS: validar propagación (dig + blackbox) y bajar TTL a 30s
3) Postgres: si primary caído, standby ya promovido (Entrega 10); revisar replicación pendiente
4) Volver al estado normal cuando primary estable: re‑seed y volver a HOT standby
```

`runbooks/dr_plan.md` (sumario)

```
- Trigger automático: p95>1.2 o 5xx>1% sost.: NO cambia; failover solo por caída real.
- Failover VRRP (<5s) / DNS (TTL 30–60s)
- RPO 15 min (WAL) – ver WAL archivado
- RTO 10–30 min – promote + Traefik apunta a standby
```

---

## 6) QA / Checklist

-

---

## 7) Próxima (Entrega 12)

- **Failover automático completo** (DNS API + health con quorum multi‑región).
- **Rotación automática** de secretos (Vault leases/periodic) y TOTP en Grafana/Traefik dashboard.
- **ETL financiero** (Data Vault 2.0 light) para analítica de alto volumen.

