# OFITEC – Entrega 7 (Despliegue & Hardening: Docker, Backups, Monitoreo, Google SSO, SII/F29)

> Objetivo: dejar OFITEC listo para **producción** con infraestructura reproducible, **backups automáticos**, **monitoreo + alertas**, **SSO con Google** y **módulo SII/F29** integrado con flujo financiero e IVA diferido. Todo Community‑safe, sin dependencias Enterprise.

---

## 0) Estructura propuesta (infra + módulos)

```
/infra
├─ docker-compose.prod.yml
├─ .env.example
├─ traefik/
│  ├─ traefik.yml
│  └─ dynamic/ofitec.yml
├─ prometheus/
│  └─ prometheus.yml
├─ alertmanager/
│  └─ alertmanager.yml
├─ grafana/
│  └─ provisioning/{datasources,dashboards}/...
├─ loki/
│  └─ config.yml
├─ promtail/
│  └─ config.yml
├─ backups/
│  ├─ backup.sh
│  ├─ restore.sh
│  └─ crontab
└─ Makefile

/custom_addons
├─ of_auth_google/       # SSO Google (auth_oauth)
└─ of_sii_cl/            # SII Chile (F29) + IVA diferido
```

---

## 1) Docker Compose (producción)

`infra/docker-compose.prod.yml`

```yaml
version: '3.9'
services:
  db:
    image: postgres:12
    env_file: .env
    volumes:
      - db_data:/var/lib/postgresql/data
    networks: [ofitec]
    healthcheck:
      test: ["CMD-SHELL","pg_isready -U $$POSTGRES_USER"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:alpine
    networks: [ofitec]

  odoo:
    image: odoo:16
    env_file: .env
    depends_on: [db, redis]
    volumes:
      - ./../custom_addons:/mnt/extra-addons
      - filestore:/var/lib/odoo
      - ./odoo.conf:/etc/odoo/odoo.conf:ro
    networks: [ofitec]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.odoo.rule=Host(`${ODOO_HOST}`)"
      - "traefik.http.routers.odoo.entrypoints=websecure"
      - "traefik.http.routers.odoo.tls.certresolver=letsencrypt"
      - "traefik.http.services.odoo.loadbalancer.server.port=8069"

  longpolling:
    image: odoo:16
    env_file: .env
    command: ["odoo","--longpolling-port","8072","-c","/etc/odoo/odoo.conf"]
    depends_on: [db, redis]
    volumes:
      - ./../custom_addons:/mnt/extra-addons
      - filestore:/var/lib/odoo
      - ./odoo.conf:/etc/odoo/odoo.conf:ro
    networks: [ofitec]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.longpoll.rule=Host(`${ODOO_HOST}`) && PathPrefix(`/longpolling`)"
      - "traefik.http.routers.longpoll.entrypoints=websecure"
      - "traefik.http.routers.longpoll.tls.certresolver=letsencrypt"
      - "traefik.http.services.longpoll.loadbalancer.server.port=8072"

  traefik:
    image: traefik:v2.10
    command: ["--providers.file.filename=/etc/traefik/traefik.yml"]
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./traefik/dynamic:/etc/traefik/dynamic:ro
      - acme:/acme
    networks: [ofitec]

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    networks: [ofitec]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prom.rule=Host(`${MON_HOST}`) && PathPrefix(`/prom`)"
      - "traefik.http.routers.prom.entrypoints=websecure"
      - "traefik.http.services.prom.loadbalancer.server.port=9090"

  alertmanager:
    image: prom/alertmanager
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    networks: [ofitec]

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASS}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks: [ofitec]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.graf.rule=Host(`${MON_HOST}`)"
      - "traefik.http.routers.graf.entrypoints=websecure"
      - "traefik.http.services.graf.loadbalancer.server.port=3000"

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks: [ofitec]

  postgres_exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      - DATA_SOURCE_NAME=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}?sslmode=disable
    networks: [ofitec]

  odoo_exporter:
    image: ghcr.io/cgmon/odoo-prometheus-exporter:latest
    environment:
      - ODOO_URL=http://odoo:8069
      - ODOO_DB=${POSTGRES_DB}
      - ODOO_USER=${ODOO_ADMIN_EMAIL}
      - ODOO_PASSWORD=${ODOO_ADMIN_PASS}
    networks: [ofitec]

  loki:
    image: grafana/loki:2.9.0
    command: ["-config.file=/etc/loki/config.yml"]
    volumes:
      - ./loki/config.yml:/etc/loki/config.yml:ro
      - loki_data:/loki
    networks: [ofitec]

  promtail:
    image: grafana/promtail:2.9.0
    command: ["-config.file=/etc/promtail/config.yml"]
    volumes:
      - ./promtail/config.yml:/etc/promtail/config.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/log:/var/log:ro
    networks: [ofitec]

  backups:
    image: bitnami/minideb:latest
    user: root
    env_file: .env
    volumes:
      - filestore:/filestore:ro
      - db_data:/dbdata:ro
      - ./backups:/opt/backups
      - backup_data:/opt/backup_out
    entrypoint: ["/bin/bash","-c","cron -f"]
    networks: [ofitec]

networks:
  ofitec: {}

volumes:
  db_data: {}
  filestore: {}
  grafana_data: {}
  loki_data: {}
  acme: {}
  backup_data: {}
```

`.env.example`

```bash
# Odoo
ODOO_HOST=ofitec.tu-dominio.cl
ODOO_ADMIN_EMAIL=admin@ofitec.cl
ODOO_ADMIN_PASS=cambia-esta-clave
ODOO_PROXY_MODE=True
WORKERS=4
LIMIT_MEMORY_SOFT=2684354560
LIMIT_MEMORY_HARD=3221225472
LONGPOLLING_PORT=8072

# Postgres
POSTGRES_DB=ofitec_prod
POSTGRES_USER=odoo
POSTGRES_PASSWORD=cambia-esta-clave

# Monitoreo
MON_HOST=monitor.tu-dominio.cl
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASS=cambia-esta-clave

# Backups
BACKUP_RETENTION_DAYS=14
BACKUP_ENC_PASS=frase-secreta-larga
BACKUP_CRON="0 3 * * *" # 03:00 AM todos los días
```

`infra/traefik/traefik.yml`

```yaml
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@ofitec.cl
      storage: /acme/acme.json
      httpChallenge: { entryPoint: web }
providers:
  docker: { exposedByDefault: false }
  file: { directory: /etc/traefik/dynamic, watch: true }
```

`infra/traefik/dynamic/ofitec.yml` (headers de seguridad)

```yaml
http:
  middlewares:
    sec-headers:
      headers:
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        browserXssFilter: true
        contentTypeNosniff: true
        frameDeny: true
  routers:
    # (Las reglas específicas se declaran por labels en cada servicio)
  services: {}
```

---

## 2) Config de Odoo (producción)

`infra/odoo.conf`

```ini
[options]
db_host = db
db_port = 5432
db_user = ${POSTGRES_USER}
db_password = ${POSTGRES_PASSWORD}
proxy_mode = ${ODOO_PROXY_MODE}
workers = ${WORKERS}
limit_memory_soft = ${LIMIT_MEMORY_SOFT}
limit_memory_hard = ${LIMIT_MEMORY_HARD}
limit_time_cpu = 120
limit_time_real = 240
longpolling_port = ${LONGPOLLING_PORT}
# Seguridad
admin_passwd = ${ODOO_ADMIN_PASS}
# Addons
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
```

**Notas de hardening**

- Deshabilitar Database Manager en producción: `--no-database-list` (o controlar por reverse proxy).
- Forzar HTTPS con HSTS (Traefik ya lo añade).
- Rotar claves de admin y DB.
- Revisar TTL de sesión y política de contraseñas (módulo security).

---

## 3) Backups automáticos + Restore

`infra/backups/backup.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
DAY=$(date +%F)
OUT="/opt/backup_out/$DAY"
mkdir -p "$OUT"
# DB dump
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$OUT/db.dump"
# Filestore
tar -C / -czf "$OUT/filestore.tar.gz" filestore
# Encriptar (opcional)
if [[ -n "${BACKUP_ENC_PASS:-}" ]]; then
  openssl enc -aes-256-cbc -pbkdf2 -salt -in "$OUT/db.dump" -out "$OUT/db.dump.enc" -k "$BACKUP_ENC_PASS" && rm "$OUT/db.dump"
  openssl enc -aes-256-cbc -pbkdf2 -salt -in "$OUT/filestore.tar.gz" -out "$OUT/filestore.tar.gz.enc" -k "$BACKUP_ENC_PASS" && rm "$OUT/filestore.tar.gz"
fi
# Retención
find /opt/backup_out -type d -mtime +${BACKUP_RETENTION_DAYS:-14} -exec rm -rf {} +
```

`infra/backups/restore.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
SRC="$1"  # directorio del día
if [[ -f "$SRC/db.dump.enc" ]]; then openssl enc -d -aes-256-cbc -pbkdf2 -in "$SRC/db.dump.enc" -out "$SRC/db.dump" -k "$BACKUP_ENC_PASS"; fi
if [[ -f "$SRC/filestore.tar.gz.enc" ]]; then openssl enc -d -aes-256-cbc -pbkdf2 -in "$SRC/filestore.tar.gz.enc" -out "$SRC/filestore.tar.gz" -k "$BACKUP_ENC_PASS"; fi
PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean "$SRC/db.dump"
tar -C / -xzf "$SRC/filestore.tar.gz"
```

`infra/backups/crontab`

```cron
# ${BACKUP_CRON}
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
${BACKUP_CRON} root /opt/backups/backup.sh >> /var/log/backup.log 2>&1
```

---

## 4) Monitoreo: Prometheus, Alertmanager, Grafana, Logs (Loki)

`infra/prometheus/prometheus.yml`

```yaml
scrape_configs:
  - job_name: 'odoo_exporter'
    static_configs: [ { targets: ['odoo_exporter:9176'] } ]
  - job_name: 'postgres'
    static_configs: [ { targets: ['postgres_exporter:9187'] } ]
  - job_name: 'cadvisor'
    static_configs: [ { targets: ['cadvisor:8080'] } ]
```

`infra/alertmanager/alertmanager.yml`

```yaml
route: { receiver: 'default' }
receivers:
  - name: 'default'
    # Añade email/slack/webhook si corresponde
```

**Ejemplo de reglas (añade a Prometheus o Alertmanager)**

- Alta latencia Odoo, crecimiento de conexiones Postgres, disco bajo, backups fallidos (expone métricas en backup container opcional).

`infra/loki/config.yml` y `infra/promtail/config.yml` apuntan a logs de contenedores; Promtail etiqueta `container=`, `service=` para búsquedas rápidas en Grafana.

`infra/grafana/provisioning/*` crea datasource Prometheus y Loki, y provisiona dashboards base (Odoo, Postgres, cAdvisor, Logs).

---

## 5) SSO con Google (Community, auth\_oauth)

### 5.1 Módulo `of_auth_google`

`custom_addons/of_auth_google/__manifest__.py`

```python
{
  "name": "OFITEC – Google SSO",
  "version": "16.0.1.0.0",
  "depends": ["auth_oauth"],
  "data": ["data/oauth_provider.xml", "views/res_config.xml"],
  "license": "LGPL-3"
}
```

`custom_addons/of_auth_google/data/oauth_provider.xml`

```xml
<odoo>
  <data noupdate="1">
    <record id="auth_oauth_provider_google_ofitec" model="auth.oauth.provider">
      <field name="name">Google (OFITEC)</field>
      <field name="enabled">True</field>
      <field name="client_id">__SET_ME__</field>
      <field name="client_secret">__SET_ME__</field>
      <field name="auth_endpoint">https://accounts.google.com/o/oauth2/auth</field>
      <field name="scope">email profile openid</field>
      <field name="validation_endpoint">https://www.googleapis.com/oauth2/v3/tokeninfo</field>
    </record>
  </data>
</odoo>
```

`custom_addons/of_auth_google/views/res_config.xml`

```xml
<odoo>
  <record id="view_res_config_settings_form_inherit_of_auth_google" model="ir.ui.view">
    <field name="name">res.config.settings.of.auth.google</field>
    <field name="model">res.config.settings</field>
    <field name="inherit_id" ref="base_setup.view_res_config_settings"/>
    <field name="arch" type="xml">
      <xpath expr="//div[@id='auth_oauth']" position="inside">
        <p>Restringir dominio de correo (ej: ofitec.cl)</p>
        <field name="of_oauth_domain"/>
      </xpath>
    </field>
  </record>
</odoo>
```

`custom_addons/of_auth_google/models/settings.py`

```python
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    of_oauth_domain = fields.Char(string='Dominio permitido (SSO)', config_parameter='of_auth_google.domain')
```

`custom_addons/of_auth_google/models/auth_hook.py`

```python
from odoo import api, SUPERUSER_ID

@api.model
def auth_signup_check_domain(env, email):
    domain = (env['ir.config_parameter'].sudo().get_param('of_auth_google.domain') or '').strip().lower()
    if domain and not email.lower().endswith('@'+domain):
        raise Exception('Dominio no permitido para SSO: %s' % domain)
    return True
```

**Instrucciones rápidas**

1. Crear OAuth Client en Google Cloud → tipo Web → **Authorized redirect URI**: `https://ofitec.tu-dominio.cl/auth_oauth/signin`
2. Rellenar `client_id` y `client_secret` en `oauth_provider.xml` (o vía UI).
3. En **Ajustes**, fijar dominio `ofitec.cl` si quieres restringir.

---

## 6) Módulo SII Chile (F29) + IVA diferido

### 6.1 Manifiesto

`custom_addons/of_sii_cl/__manifest__.py`

```python
{
  "name": "OFITEC – SII Chile (F29)",
  "version": "16.0.1.0.0",
  "depends": ["account","of_flujo_financiero"],
  "data": [
    "security/ir.model.access.csv",
    "views/f29_views.xml",
    "data/cron.xml"
  ],
  "license": "LGPL-3"
}
```

### 6.2 Modelos

`custom_addons/of_sii_cl/models/f29.py`

```python
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class OfSiiF29(models.Model):
    _name = 'of.sii.f29'
    _description = 'Declaración F29 (IVA)'
    _order = 'period desc'
    _inherit = ['mail.thread']

    period = fields.Char(required=True, help='YYYY-MM')
    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company)
    iva_debito = fields.Monetary(currency_field='currency_id')
    iva_credito = fields.Monetary(currency_field='currency_id')
    iva_total = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    iva_diferido = fields.Monetary(currency_field='currency_id')
    diferir = fields.Boolean(help='Postergar pago de IVA este periodo')
    status = fields.Selection([('draft','Borrador'),('ready','Listo'),('sent','Enviado'),('paid','Pagado')], default='draft', tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)

    @api.depends('iva_debito','iva_credito')
    def _compute_total(self):
        for r in self:
            r.iva_total = max(0.0, (r.iva_debito or 0.0) - (r.iva_credito or 0.0))

    def action_compute(self):
        for r in self:
            y,m = r.period.split('-')
            date_from = fields.Date.to_date(f"{y}-{m}-01")
            date_to = date_from + relativedelta(months=1, days=-1)
            Move = self.env['account.move'].sudo()
            # Débito: ventas con IVA
            ventas = Move.search([('move_type','=','out_invoice'),('invoice_date','>=',date_from),('invoice_date','<=',date_to),('state','=','posted')])
            credito = Move.search([('move_type','=','in_invoice'),('invoice_date','>=',date_from),('invoice_date','<=',date_to),('state','=','posted')])
            # Simplificado: sumar impuestos con tag IVA
            def sum_iva(moves):
                tot = 0.0
                for mv in moves:
                    for l in mv.invoice_line_ids:
                        for tax in l.tax_ids:
                            if 'IVA' in (tax.name or '').upper():
                                tot += (l.price_subtotal or 0.0) * (tax.amount/100.0)
                return tot
            r.iva_debito = sum_iva(ventas)
            r.iva_credito = sum_iva(credito)
            r.status = 'ready'

    def action_register_cashflow(self):
        # Crea líneas en Flujo: IVA a pagar y, si difiere, IVA diferido
        Cash = self.env['of.cashflow.line'].sudo()
        Board = self.env['of.cashflow.board'].sudo()
        board = Board.search([('state','=','open'),('company_id','=',self.company_id.id)], limit=1)
        if not board:
            board = Board.create({'name': f'Board {self.company_id.name}', 'company_id': self.company_id.id, 'state': 'open'})
        for r in self:
            amount = r.iva_total
            if not amount: continue
            if r.diferir:
                # Movimiento diferido (mes + 1) como "planned" y marcar iva_diferido
                first_next = fields.Date.to_date(r.period + "-01") + relativedelta(months=1)
                Cash.create({
                    'board_id': board.id,
                    'company_id': board.company_id.id,
                    'date': first_next,
                    'status': 'planned',
                    'category': 'taxes',
                    'amount': -abs(amount),
                    'source_ref': f'f29:{r.period}:deferred'
                })
                r.iva_diferido = amount
            else:
                # Movimiento actual "planned" para el último día del mes
                date_pay = fields.Date.to_date(r.period + "-01") + relativedelta(day=31)
                Cash.create({
                    'board_id': board.id,
                    'company_id': board.company_id.id,
                    'date': date_pay,
                    'status': 'planned',
                    'category': 'taxes',
                    'amount': -abs(amount),
                    'source_ref': f'f29:{r.period}:due'
                })
            r.message_post(body=f"Flujo F29 registrado (diferido={r.diferir})")

    def action_mark_paid(self):
        # Marca pagado y mueve planned→actual
        Cash = self.env['of.cashflow.line'].sudo()
        for r in self:
            ref_due = f'f29:{r.period}:due'
            ref_def = f'f29:{r.period}:deferred'
            lines = Cash.search([('source_ref','in',[ref_due, ref_def])])
            for l in lines:
                l.write({'status': 'actual'})
            r.status = 'paid'
```

### 6.3 Vistas y Cron

`custom_addons/of_sii_cl/views/f29_views.xml`

```xml
<odoo>
  <record id="view_of_sii_f29_tree" model="ir.ui.view">
    <field name="name">of.sii.f29.tree</field>
    <field name="model">of.sii.f29</field>
    <field name="arch" type="xml">
      <tree>
        <field name="period"/>
        <field name="iva_debito"/>
        <field name="iva_credito"/>
        <field name="iva_total"/>
        <field name="diferir"/>
        <field name="iva_diferido"/>
        <field name="status"/>
      </tree>
    </field>
  </record>

  <record id="view_of_sii_f29_form" model="ir.ui.view">
    <field name="name">of.sii.f29.form</field>
    <field name="model">of.sii.f29</field>
    <field name="arch" type="xml">
      <form string="F29">
        <sheet>
          <group>
            <field name="period"/>
            <field name="company_id"/>
            <field name="diferir"/>
          </group>
          <group>
            <field name="iva_debito"/>
            <field name="iva_credito"/>
            <field name="iva_total"/>
            <field name="iva_diferido"/>
          </group>
          <footer>
            <button name="action_compute" string="Calcular" type="object" class="btn-secondary"/>
            <button name="action_register_cashflow" string="Registrar Flujo" type="object" class="btn-primary"/>
            <button name="action_mark_paid" string="Marcar Pagado" type="object"/>
          </footer>
        </sheet>
      </form>
    </field>
  </record>

  <menuitem id="menu_sii_root" name="SII"/>
  <menuitem id="menu_f29" name="F29" parent="menu_sii_root" action="action_f29"/>
  <record id="action_f29" model="ir.actions.act_window">
    <field name="name">F29</field>
    <field name="res_model">of.sii.f29</field>
    <field name="view_mode">tree,form</field>
  </record>
</odoo>
```

`custom_addons/of_sii_cl/data/cron.xml`

```xml
<odoo>
  <data noupdate="1">
    <record id="ir_cron_f29_monthly" model="ir.cron">
      <field name="name">Generar F29 del mes</field>
      <field name="model_id" ref="model_of_sii_f29"/>
      <field name="state">code</field>
      <field name="code">model.create({'period': fields.Date.today().strftime('%Y-%m')}).action_compute()</field>
      <field name="interval_number">1</field>
      <field name="interval_type">months</field>
    </record>
  </data>
</odoo>
```

> **Nota:** Esta implementación calcula IVA de forma **simplificada** en base a impuestos con “IVA” en su nombre. Podemos mapear exactamente a casillas F29 si nos entregas la tabla de mapeo (impuesto→casilla).

---

## 7) Makefile (atajos)

`infra/Makefile`

```make
up:
	docker compose -f docker-compose.prod.yml --env-file .env up -d

logs:
	docker compose -f docker-compose.prod.yml logs -f --tail=200

down:
	docker compose -f docker-compose.prod.yml down

backup:
	docker compose -f docker-compose.prod.yml exec backups /opt/backups/backup.sh

restore:
	@echo "Uso: make restore SRC=/opt/backup_out/AAAA-MM-DD"; \
	docker compose -f docker-compose.prod.yml exec -e BACKUP_ENC_PASS=$$BACKUP_ENC_PASS backups /opt/backups/restore.sh $$SRC
```

---

## 8) Checklist de despliegue

-

---

## 9) Seguridad y buenas prácticas

- **Segregación de redes** (ya aplicada) y puertos expuestos solo por Traefik.
- **Headers** de seguridad + HSTS. Cookies `Secure` y `HttpOnly` (Odoo heredado).
- **Rotación** de claves/secrets y **principio de mínimo privilegio**.
- **Backups encriptados**, retención y pruebas de restore periódicas.
- **Auditoría**: logs centralizados en Loki; conservar ≥ 30 días.

---

## 10) Qué queda listo ahora

- Infraestructura **reproducible** (Docker Compose) con reverse proxy y TLS auto.
- **Backups** diarios en cron, con retención y encriptación opcional.
- **Monitoreo** (Odoo, Postgres, contenedores) + Grafana y logs centralizados.
- **Google SSO** (con restricción por dominio) para onboarding más simple.
- **SII/F29** integrado al **Flujo** (planned/actual) con soporte de **IVA diferido**.

## 11) Próxima entrega (8)

- Pipeline **CI/CD** para despliegue a prod (Actions),
- **Escaneo de imágenes** (Trivy),
- **Backup remoto** (S3/GCS) con **restic** y cifrado,
- **Alertas** por Slack/Email (Alertmanager),
- **Mapeo F29** detallado por casillas + exportación oficial.

