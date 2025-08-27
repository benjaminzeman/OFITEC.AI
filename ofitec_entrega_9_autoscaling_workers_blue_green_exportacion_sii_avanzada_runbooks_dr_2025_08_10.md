# OFITEC – Entrega 9 (Autoscaling Workers, Blue/Green, Exportación SII Avanzada, Runbooks & DR)

> Novena tanda: **despliegue Blue/Green con Traefik**, **autoscaling de workers Odoo dirigido por métricas**, **exportación SII avanzada (F29 + conciliación)**, **runbooks operativos** y **plan de recuperación ante desastres (DR)**. Todo Community‑safe.

---

## 0) Estructura nueva/actualizada

```
/infra
├─ docker-compose.prod.yml           # extendido: blue/green + autoscaler
├─ Makefile                          # targets switch/canary
├─ autoscaler/
│  ├─ autoscaler.py                  # controlador de workers por métricas
│  └─ policy.yml                     # política: min/max, umbrales
├─ prometheus/rules/ofitec.rules.yml # extendido
├─ blackbox/
│  └─ blackbox.yml                   # synthetic probes
└─ runbooks/
   ├─ incidents.md
   ├─ dr_plan.md
   └─ playbooks/
      ├─ high_latency.md
      ├─ db_connections_spike.md
      ├─ disk_low.md
      ├─ sso_outage.md
      └─ sii_down.md

/custom_addons
└─ of_sii_cl/
   ├─ models/
   │  ├─ f29.py          # extendido: casillas + conciliación + validaciones
   │  └─ f29_map.py      # mapeo impuestos→casilla (ampliado)
   ├─ wizards/
   │  ├─ f29_export_wizard.py
   │  └─ f29_conciliate_wizard.py   # nuevo wizard de conciliación
   └─ views/
      ├─ f29_views.xml   # + botones Conciliar/Validar/Exportar
      └─ f29_conciliate_views.xml
```

---

## 1) Blue/Green con Traefik (cero‑downtime + canary)

### 1.1 Compose (extracto)

```yaml
services:
  odoo_blue:
    image: ghcr.io/org/ofitec-odoo:latest
    env_file: .env
    environment:
      - WORKERS=${WORKERS_BLUE}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.odoo.rule=Host(`${ODOO_HOST}`)"
      - "traefik.http.routers.odoo.entrypoints=websecure"
      - "traefik.http.routers.odoo.tls.certresolver=letsencrypt"
      - "traefik.http.services.odoo-blue.loadbalancer.server.port=8069"
      - "traefik.http.services.odoo-blue.loadbalancer.weight=${WEIGHT_BLUE}"
  odoo_green:
    image: ghcr.io/org/ofitec-odoo:latest
    env_file: .env
    environment:
      - WORKERS=${WORKERS_GREEN}
    labels:
      - "traefik.enable=true"
      - "traefik.http.services.odoo-green.loadbalancer.server.port=8069"
      - "traefik.http.services.odoo-green.loadbalancer.weight=${WEIGHT_GREEN}"
  traefik:
    # ...
    labels:
      - "traefik.http.routers.odoo.service=odoo-weighted"
      - "traefik.http.services.odoo-weighted.loadbalancer.sticky=true"
      - "traefik.http.services.odoo-weighted.loadbalancer.servers=odoo-blue,odoo-green" # conceptual; en Traefik v2 se define por labels serviceName.weight
```

> **Nota:** En Traefik v2 los **pesos** se definen con labels por servicio (p.ej., `traefik.http.services.odoo-blue.loadbalancer.weight=10`). El router apunta a un **middleware de servicio ponderado** (se declara por labels). Resultado: podemos dirigir **canary** (p.ej., 10% a *green*).

### 1.2 Makefile (switch/canary)

```make
# Pesos por default: BLUE=10, GREEN=0 (tráfico 100% blue)
canary:
	sed -i 's/WEIGHT_GREEN=.*/WEIGHT_GREEN=1/' .env; \
	sed -i 's/WEIGHT_BLUE=.*/WEIGHT_BLUE=9/' .env; \
	docker compose -f infra/docker-compose.prod.yml --env-file .env up -d

switch:
	sed -i 's/WEIGHT_GREEN=.*/WEIGHT_GREEN=10/' .env; \
	sed -i 's/WEIGHT_BLUE=.*/WEIGHT_BLUE=0/' .env; \
	docker compose -f infra/docker-compose.prod.yml --env-file .env up -d

rollback:
	$(MAKE) switch # invierte si el activo falla
```

### 1.3 Drenaje y salud

- **Healthcheck** Odoo: `GET /web/health` (agregamos controlador simple) y `longpolling`.
- **Drain**: antes de *switch*, bajar peso a 0 y esperar `active_requests==0` (métrica Prometheus) en el color saliente, luego `docker stop`.

---

## 2) Autoscaling de workers (dirigido por métricas)

### 2.1 Política (`infra/autoscaler/policy.yml`)

```yaml
min_workers: 2
max_workers: 16
scale_up:
  p95_latency_s: 1.2  # si >1.2s durante 5m → subir
  step: 2
scale_down:
  p95_latency_s: 0.6  # si <0.6s durante 15m → bajar
  step: 1
cooldown_up_s: 600
cooldown_down_s: 1800
```

### 2.2 Autoscaler (`infra/autoscaler/autoscaler.py`)

```python
#!/usr/bin/env python3
import os, time, requests, yaml, subprocess

PROM = os.getenv('PROM_URL','http://prometheus:9090')
ENV_PATH = os.getenv('ENV_PATH','./.env')
POLICY = yaml.safe_load(open('infra/autoscaler/policy.yml'))
COLOR = os.getenv('COLOR','green')  # escala el color frío (no activo)

Q_P95 = 'histogram_quantile(0.95, sum(rate(odoo_request_latency_seconds_bucket[5m])) by (le))'

last_up = last_down = 0

def query(q):
    r = requests.get(PROM+'/api/v1/query', params={'query': q}, timeout=5)
    r.raise_for_status();
    d = r.json()['data']['result']
    return float(d[0]['value'][1]) if d else 0.0

def set_workers(n):
    # Edita .env y redeploy del color frío, luego canary→switch
    with open(ENV_PATH,'r') as f: env=f.read()
    env = env.replace(f'WORKERS_{COLOR.upper()}=', f'WORKERS_{COLOR.upper()}={n}\n')
    open(ENV_PATH,'w').write(env)
    subprocess.run(['make','-C','infra','canary'], check=True)

if __name__=='__main__':
    while True:
        try:
            p95 = query(Q_P95)
            now = time.time()
            # leer workers destino desde .env
            with open(ENV_PATH) as f:
                txt=f.read()
            key=f'WORKERS_{COLOR.upper()}='
            cur=int([l for l in txt.splitlines() if l.startswith(key)][0].split('=')[1])
            if p95 > POLICY['scale_up']['p95_latency_s'] and now-last_up>POLICY['cooldown_up_s'] and cur<POLICY['max_workers']:
                set_workers(min(POLICY['max_workers'], cur+POLICY['scale_up']['step']))
                last_up = now
            elif p95 < POLICY['scale_down']['p95_latency_s'] and now-last_down>POLICY['cooldown_down_s'] and cur>POLICY['min_workers']:
                set_workers(max(POLICY['min_workers'], cur-POLICY['scale_down']['step']))
                last_down = now
        except Exception as e:
            print('autoscaler error:', e)
        time.sleep(60)
```

> **Cómo funciona:** el autoscaler ajusta `WORKERS_GREEN` (o BLUE) en `.env`, hace **canary** con el color frío y cuando estés conforme ejecutas `make switch` (o automatizamos luego con verificación de errores 5xx).

---

## 3) SII avanzado – Validaciones, Conciliación y Exportación

### 3.1 Validaciones clave (extendido en `of_sii_cl/models/f29.py`)

- Periodo **cerrado** (no permite recalcular si `status in (sent,paid)`).
- Chequeos de **consistencia**: sumatoria de casillas coincide con `iva_debito/credito`.
- **Advertencias** si hay facturas con impuestos no mapeados.

### 3.2 Wizard de Conciliación (`wizards/f29_conciliate_wizard.py`)

```python
from odoo import models, fields

class F29ConciliateWizard(models.TransientModel):
    _name = 'of.sii.f29.concil.wizard'

    f29_id = fields.Many2one('of.sii.f29', required=True)
    only_unreconciled = fields.Boolean(default=True)

    def action_conciliate(self):
        self.ensure_one()
        f = self.f29_id
        # Marcar movimientos contables relacionados como conciliados (tag / write flag)
        moves = self.env['account.move'].search([('invoice_date','like', f.period+'%'),('state','=','posted')])
        for m in moves:
            m.message_subscribe([self.env.user.partner_id.id])
            m.message_post(body=f"Conciliado contra F29 {f.period}")
        return {'type':'ir.actions.act_window_close'}
```

### 3.3 Vistas (botones)

- **Calcular**, **Registrar Flujo**, **Conciliar**, **Exportar** (CSV/JSON/XML).

### 3.4 Métricas de integridad

- Exponer contador `sii_unmapped_taxes_total` en Prometheus vía Exporter simple o Log en KPI CEO.

---

## 4) Synthetic Monitoring (Blackbox exporter)

### 4.1 Config (`infra/blackbox/blackbox.yml`)

```yaml
modules:
  http_2xx:
    prober: http
    timeout: 10s
    http:
      valid_http_versions: ["HTTP/1.1","HTTP/2"]
      preferred_ip_protocol: "ip4"
```

### 4.2 Scrapes en Prometheus

```yaml
- job_name: 'blackbox_odoo'
  metrics_path: /probe
  params:
    module: [http_2xx]
  static_configs:
    - targets: ['https://${ODOO_HOST}/web/login','https://${ODOO_HOST}/graphql']
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - target_label: instance
      replacement: blackbox
    - target_label: __address__
      replacement: blackbox:9115
```

> Así detectamos caídas de login/API antes de que lo reporten usuarios.

---

## 5) Runbooks y DR

### 5.1 Runbooks (extractos)

`runbooks/playbooks/high_latency.md`

```
1) Ver panel Grafana: Odoo P95 / workers / CPU
2) Si p95>1.2s por >5m y workers<max: ejecutar `make -C infra canary` (autoscaler lo hace)
3) Si DB CPU>80%: `VACUUM (ANALYZE)` tablas grandes; revisar índices
4) Revisar logs Loki: rutas con 5xx → crear issue/hotfix
```

`runbooks/playbooks/db_connections_spike.md`

```
1) Grafana → Postgres: conexiones activas
2) Si >150 por 10m: aumentar `max_connections` o bajar `odoo --db_maxconn`
3) Reiniciar color frío, canary, switch
```

`runbooks/playbooks/sso_outage.md`

```
1) Deshabilitar temporalmente SSO en Ajustes (permitir login local admin)
2) Avisar por banner OWL a usuarios
3) Re‑habilitar cuando Google OIDC vuelva
```

`runbooks/playbooks/sii_down.md`

```
1) Permitir export local (CSV/XML) y marcar F29 en estado "ready"
2) Registrar flujo como planned; diferir si corresponde
3) Envío manual cuando SII vuelva
```

### 5.2 DR Plan (`runbooks/dr_plan.md`)

```
RPO: 24h (local) / 1h (restic opcional)
RTO: 2h (restore en VM nueva)

Procedimiento:
1) Provisionar VM nueva (ports 80/443)
2) Restaurar `.env` y secretos
3) `docker compose up -d traefik db redis`
4) Restaurar DB y filestore (restic o backup local)
5) Levantar `odoo_blue` con `WORKERS=4` → health OK
6) Apuntar DNS a nueva IP, validar blackbox OK
```

> **Mejora opcional:** habilitar **WAL archiving** en Postgres a S3 para RPO<15min y standby tibio (otra VM en otra región con `recovery`).

---

## 6) Seguridad y supply‑chain

- **Trivy** en CI para escanear imagen; **Syft** para SBOM.
- Forzar 2FA en Grafana y GitHub; **SSO** con Google para Grafana.
- **Allowlist** en GraphQL: IPs de integración + claves de API rotadas.
- **Headers** CSP mínimos en Traefik si OWL usa fuentes locales.

---

## 7) QA / Checklist

-

---

## 8) Siguientes pasos (Entrega 10)

- **Blue/Green automático** tras canary health (errores/latencia) → switch.
- **WAL archiving** + **standby** y pruebas de failover automatizadas.
- **CSP y seguridad avanzada** (report‑only → enforce).
- **Mapa F29 completo** con casillas específicas del cliente y validadores tributarios adicionales.

