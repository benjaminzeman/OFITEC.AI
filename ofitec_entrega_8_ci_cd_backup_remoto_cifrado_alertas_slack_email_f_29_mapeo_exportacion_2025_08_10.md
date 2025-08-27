# OFITEC – Entrega 8 (CI/CD, Backup remoto cifrado, Alertas Slack/Email, F29 mapeo & exportación)

> Octava tanda: **pipeline CI/CD** de despliegue, **backup remoto cifrado** (S3/GCS) con **restic**, **alertas** por Slack/Email (Alertmanager) y **mapeo detallado F29 por casillas** con **exportación** (CSV/JSON/XML). Community‑safe.

---

## 0) Contenido y ubicación

```
/infra
├─ .env.example            # + claves CI/CD/Backup
├─ docker-compose.prod.yml # (Entrega 7) – extendido
├─ Makefile                # deploy/rollback
├─ prometheus/
│  ├─ prometheus.yml
│  └─ rules/ofitec.rules.yml        # <<< NUEVO: reglas de alertas
├─ alertmanager/
│  └─ alertmanager.yml              # <<< Slack/Email
├─ backups/
│  ├─ backup.sh                     # local (Entrega 7)
│  ├─ restic-backup.sh              # <<< a S3/GCS + forget/prune
│  └─ crontab
└─ deploy/
   ├─ Dockerfile                    # <<< imagen ofitec-odoo
   └─ entrypoint.sh                 # hook migraciones opcional

/.github/workflows
└─ deploy.yml                       # <<< CI/CD a prod

/custom_addons
└─ of_sii_cl/                       # (Entrega 7)
   ├─ models/
   │  ├─ f29.py                     # extendido – casillas y export
   │  └─ f29_map.py                 # <<< mapeo de impuestos→casillas
   ├─ data/f29_mapping.yml          # <<< archivo de mapeo
   ├─ wizards/f29_export_wizard.py  # <<< exportador
   └─ views/
      ├─ f29_views.xml              # extendido – botones export
      └─ f29_export_views.xml       # <<< wizard
```

---

## 1) CI/CD – GitHub Actions → servidor Docker/Traefik

### 1.1 Dockerfile de aplicación (`infra/deploy/Dockerfile`)

```dockerfile
FROM odoo:16
# Paquetes extra (ej: or-tools, libs gráficas mínimas)
RUN pip install --no-cache-dir ortools==9.8.0 graphene==3.3
# Copy addons
COPY ./custom_addons /mnt/extra-addons
# Entrypoint opcional para migraciones/health
COPY ./infra/deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["odoo","-c","/etc/odoo/odoo.conf"]
```

`infra/deploy/entrypoint.sh`

```bash
#!/usr/bin/env bash
set -e
if [[ "${UPGRADE_MODULES:-}" != "" ]]; then
  echo "Running upgrades: $UPGRADE_MODULES"
  odoo -c /etc/odoo/odoo.conf -u "$UPGRADE_MODULES" --stop-after-init || true
fi
exec "$@"
```

### 1.2 Workflow (`.github/workflows/deploy.yml`)

```yaml
name: Deploy OFITEC
on:
  push:
    branches: [ main ]
  workflow_dispatch: {}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-qemu-action@v3
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GHCR_TOKEN }}
      - name: Build & Push
        uses: docker/build-push-action@v6
        with:
          context: .
          file: infra/deploy/Dockerfile
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/ofitec-odoo:latest
            ghcr.io/${{ github.repository_owner }}/ofitec-odoo:${{ github.sha }}
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Copy compose & env
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          source: "infra/docker-compose.prod.yml,infra/odoo.conf,infra/.env.example,infra/Makefile"
          target: "~/ofitec/"
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            set -e
            cd ~/ofitec
            cp .env.example .env
            sed -i "s|ghcr.io/.*/ofitec-odoo:latest|ghcr.io/${{ github.repository_owner }}/ofitec-odoo:${{ github.sha }}|" docker-compose.prod.yml
            docker compose -f docker-compose.prod.yml --env-file .env pull
            docker compose -f docker-compose.prod.yml --env-file .env up -d --remove-orphans
            docker system prune -af || true
```

**Secrets necesarios**: `GHCR_TOKEN`, `SSH_HOST`, `SSH_USER`, `SSH_KEY` (PEM), `SSH_KNOWN_HOSTS` (opcional).

---

## 2) Backup remoto cifrado con Restic (S3/GCS)

### 2.1 Script (`infra/backups/restic-backup.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${RESTIC_REPOSITORY:?need}" : "${RESTIC_PASSWORD:?need}"
# AWS_*/GCS_* variables según backend
DAY=$(date +%F)
WORK=/tmp/ofitec-bak-$DAY
mkdir -p "$WORK"
# DB dump
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$WORK/db.dump"
# Filestore
sudo tar -C / -czf "$WORK/filestore.tar.gz" filestore
export RESTIC_PASSWORD
restic -r "$RESTIC_REPOSITORY" backup "$WORK" --tag ofitec --host prod-odoo
restic -r "$RESTIC_REPOSITORY" forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
rm -rf "$WORK"
```

### 2.2 Compose – contenedor backup con restic (extensión a `docker-compose.prod.yml`)

```yaml
  restic:
    image: restic/restic:latest
    env_file: .env
    volumes:
      - filestore:/filestore:ro
      - db_data:/dbdata:ro
      - ./backups:/opt/backups
    entrypoint: ["/bin/bash","-c","cron -f"]
```

`.env` (campos nuevos)

```bash
# RESTIC (S3 ejemplo)
RESTIC_REPOSITORY=s3:https://s3.amazonaws.com/ofitec-backups
RESTIC_PASSWORD=frase-larga-secreta
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

> **Restore**: `restic -r $RESTIC_REPOSITORY snapshots` → `restic restore latest --target /restore`, luego restaurar `db.dump` y `filestore.tar.gz` (igual que `restore.sh`).

---

## 3) Alertas – Prometheus Rules + Alertmanager Slack/Email

### 3.1 Reglas (`infra/prometheus/rules/ofitec.rules.yml`)

```yaml
groups:
- name: ofitec
  rules:
  - alert: OdooHighLatency
    expr: histogram_quantile(0.95, sum(rate(odoo_request_latency_seconds_bucket[5m])) by (le)) > 1.5
    for: 5m
    labels: { severity: warning }
    annotations: { summary: "P95 latencia Odoo > 1.5s", description: "Revisar carga y workers" }

  - alert: PostgresConnectionsHigh
    expr: pg_stat_activity_count > 150
    for: 5m
    labels: { severity: warning }

  - alert: DiskSpaceLow
    expr: (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes) < 0.1
    for: 10m
    labels: { severity: critical }

  - alert: BackupResticFailure
    expr: increase(process_start_time_seconds{job="restic"}[1d]) < 1
    for: 1d
    labels: { severity: warning }
    annotations: { summary: "Restic no corrió en 24h" }
```

Añadir a `prometheus.yml`:

```yaml
rule_files:
  - /etc/prometheus/rules/ofitec.rules.yml
```

### 3.2 Alertmanager (`infra/alertmanager/alertmanager.yml`)

```yaml
route:
  receiver: 'slack'
  routes:
    - matchers:
      - severity = critical
      receiver: 'email'
receivers:
  - name: 'slack'
    slack_configs:
      - send_resolved: true
        api_url: ${SLACK_WEBHOOK}
        channel: '#alertas-ofitec'
        title: '[OFITEC] {{ .CommonLabels.alertname }}'
        text: '{{ range .Alerts }}*{{ .Annotations.summary }}* – {{ .Labels.severity }}\n{{ end }}'
  - name: 'email'
    email_configs:
      - to: ops@ofitec.cl
        from: alertas@ofitec.cl
        smarthost: smtp.sendgrid.net:587
        auth_username: apikey
        auth_password: ${SMTP_APIKEY}
```

`.env` (campos nuevos)

```bash
SLACK_WEBHOOK=https://hooks.slack.com/services/...
SMTP_APIKEY=SG.XXXXX
```

---

## 4) F29 – mapeo por casillas y exportación

### 4.1 Modelo de mapeo (`custom_addons/of_sii_cl/models/f29_map.py`)

```python
from odoo import models, fields

class OfSiiF29Map(models.Model):
    _name = 'of.sii.f29.map'
    _description = 'Mapeo F29 (impuesto → casilla)'

    name = fields.Char(required=True)
    tax_id = fields.Many2one('account.tax', required=True)
    casilla = fields.Char(required=True)  # ej. '29', '30', '89'
    tipo = fields.Selection([('debito','Débito'),('credito','Crédito')], required=True)
```

### 4.2 Datos de arranque (`custom_addons/of_sii_cl/data/f29_mapping.yml`)

```yaml
# ejemplo mínimo – adaptar a la realidad del cliente
- name: IVA Débito 19%
  tax_xmlid: account.tax_iva_19
  casilla: '29'
  tipo: debito
- name: IVA Crédito 19%
  tax_xmlid: account.tax_iva_19_compra
  casilla: '49'
  tipo: credito
```

### 4.3 Extensión de cálculo y export (`custom_addons/of_sii_cl/models/f29.py`)

```python
# ... dentro de OfSiiF29.action_compute()
Map = self.env['of.sii.f29.map'].sudo()
# Construir índice tax_id->casilla
midx = {}
for m in Map.search([]):
    midx[m.tax_id.id] = (m.casilla, m.tipo)

# Barrer facturas y acumular por casilla
acum = {}
for mv in ventas:
    for l in mv.invoice_line_ids:
        for tax in l.tax_ids:
            k = midx.get(tax.id)
            if not k: continue
            cas, tipo = k
            base = l.price_subtotal or 0.0
            monto = base * (tax.amount/100.0)
            acum[cas] = acum.get(cas, 0.0) + (monto if tipo=='debito' else 0.0)
for mv in credito:
    for l in mv.invoice_line_ids:
        for tax in l.tax_ids:
            k = midx.get(tax.id)
            if not k: continue
            cas, tipo = k
            base = l.price_subtotal or 0.0
            monto = base * (tax.amount/100.0)
            if tipo=='credito':
                acum[cas] = acum.get(cas, 0.0) + monto
# Guardar totales principales
self.iva_debito = sum(v for c,v in acum.items() if c in ('29','30'))
self.iva_credito = sum(v for c,v in acum.items() if c in ('49','50'))
self.status = 'ready'
self.message_post(body=f"F29 mapeado casillas: {sorted(acum.items())[:5]}…")

# Export helpers
def to_csv(self):
    import io, csv
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(['casilla','monto'])
    for cas, val in sorted(acum.items()):
        w.writerow([cas, f"{val:.2f}"])
    return buf.getvalue()

def to_json(self):
    import json
    return json.dumps({'period': self.period, 'company': self.company_id.name, 'casillas': acum}, ensure_ascii=False)

def to_xml(self):
    from xml.etree.ElementTree import Element, SubElement, tostring
    root = Element('F29'); SubElement(root,'Period').text = self.period
    for cas, val in sorted(acum.items()):
        n = SubElement(root,'Casilla', num=str(cas)); n.text = f"{val:.2f}"
    return tostring(root, encoding='utf-8')
```

### 4.4 Wizard de exportación (`custom_addons/of_sii_cl/wizards/f29_export_wizard.py`)

```python
from odoo import models, fields
import base64

class F29ExportWizard(models.TransientModel):
    _name = 'of.sii.f29.export.wizard'

    f29_id = fields.Many2one('of.sii.f29', required=True)
    fmt = fields.Selection([('csv','CSV'),('json','JSON'),('xml','XML')], default='csv')
    filedata = fields.Binary(readonly=True)
    filename = fields.Char(readonly=True)

    def action_export(self):
        self.ensure_one()
        r = self.f29_id
        if self.fmt=='csv': data=r.to_csv(); ext='csv'
        elif self.fmt=='json': data=r.to_json(); ext='json'
        else: data=r.to_xml(); ext='xml'
        self.write({'filedata': base64.b64encode(data if isinstance(data, bytes) else data.encode('utf-8')),
                    'filename': f'F29_{r.period}.{ext}'})
        return {
          'type':'ir.actions.act_window', 'res_model':'of.sii.f29.export.wizard', 'view_mode':'form', 'res_id': self.id, 'target':'new'
        }
```

### 4.5 Vistas (botón Exportar)

`custom_addons/of_sii_cl/views/f29_export_views.xml`

```xml
<odoo>
  <record id="view_f29_export_wizard" model="ir.ui.view">
    <field name="name">of.sii.f29.export.wizard</field>
    <field name="model">of.sii.f29.export.wizard</field>
    <field name="arch" type="xml">
      <form string="Exportar F29">
        <group>
          <field name="fmt"/>
          <field name="filedata" filename="filename" readonly="1"/>
          <field name="filename" readonly="1"/>
        </group>
        <footer>
          <button name="action_export" string="Generar" type="object" class="btn-primary"/>
          <button string="Cerrar" class="btn-secondary" special="cancel"/>
        </footer>
      </form>
    </field>
  </record>
</odoo>
```

Extensión en `f29_views.xml` (botón):

```xml
<footer position="inside">
  <button name="%(view_f29_export_wizard)d" string="Exportar" type="action" class="btn-secondary"/>
</footer>
```

> **Nota:** si el SII publica un formato electrónico específico, podemos adaptar `to_xml()` a su esquema.

---

## 5) Makefile – despliegue/rollback rápido

`infra/Makefile` (extensión)

```make
.PHONY: deploy rollback

TAG?=latest

deploy:
	@sed -i "s|ghcr.io/.*/ofitec-odoo:.*|ghcr.io/${OWNER}/ofitec-odoo:${TAG}|" docker-compose.prod.yml; \
	docker compose -f docker-compose.prod.yml --env-file .env pull; \
	docker compose -f docker-compose.prod.yml --env-file .env up -d --remove-orphans

rollback:
	@$(MAKE) deploy TAG=$(PREV)
```

---

## 6) QA rápida

- **CI/CD**: push a `main` → construye imagen y actualiza el stack remoto.
- **Restic**: `restic snapshots` muestra backups; simular restore.
- **Alertas**: detener `odoo_exporter` y verificar alerta en Slack; forzar `BackupResticFailure` cambiando cron.
- **F29**: cargar mapeo base, ejecutar **Calcular** y **Exportar** (CSV/JSON/XML); verificar líneas en **Flujo** planned/actual.

---

## 7) Seguridad y secretos

- Guardar credenciales (SSH, GHCR, Slack, SMTP, S3/GCS) **solo** en **GitHub Secrets** y `.env` del servidor.
- Rotación semestral de `RESTIC_PASSWORD`/tokens; validar `forget/prune` después de rotar.

---

## 8) Próximo (Entrega 9)

- **Autoscaling** por cargas (workers),
- **Blue/Green** o **Canary** en Compose (dos servicios + label swap),
- **Exportación SII** avanzada (formularios anexos y conciliación),
- **Runbooks** (procedimientos incidentes) y **DR Plan** (RPO/RTO definidos).

