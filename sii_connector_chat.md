# 🗂 Chat del módulo sii_connector

> **Objetivo:** Integrar con los Web Services del SII en Chile para extraer registros de compras (RC) y ventas (RV), reconstruir reportes F29 y generar pasivos de IVA en el flujo de caja.

## 1. Estructura del addon
```
sii_connector/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── sii_credential.py
│   └── sii_service.py
├── data/
│   ├── ir_cron_sii.xml
│   └── sii_menu.xml
├── views/
│   ├── sii_credential_views.xml
│   └── sii_service_settings.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    └── test_sii_connector.py
```

## 2. __manifest__.py
```python
{
    'name': 'SII Connector',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Integration',
    'summary': 'Conecta con el SII para extraer RC, RV y generar F29 en flujo de caja',
    'depends': ['ofitec_security', 'flow_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/sii_menu.xml',
        'data/ir_cron_sii.xml',
        'views/sii_credential_views.xml',
        'views/sii_service_settings.xml',
    ],
    'installable': True,
    'application': False,
}
```

## 3. Modelos

### 3.1 sii_credential.py
```python
from odoo import models, fields, api

class SiiCredential(models.Model):
    _name = 'sii_connector.credential'
    _description = 'Credenciales para conexión SII'

    name = fields.Char(string='Nombre', required=True)
    credential_id = fields.Many2one('ofitec_security.digital_credential', string='Credencial Digital', required=True)
    endpoint = fields.Char(string='Endpoint SOAP', required=True, default='https://palena.sii.cl/DTEWS/RegistroDTE.jws?wsdl')
    active = fields.Boolean(string='Activo', default=True)

    @api.model
def get_active(self):
        return self.search([('active','=',True)], limit=1)
```

### 3.2 sii_service.py
```python
from odoo import models, api, fields
from zeep import Client
from zeep.transports import Transport
from requests import Session

class SiiService(models.Model):
    _name = 'sii_connector.service'
    _description = 'Servicio SII Web Services'

    @api.model
def _get_client(self):
        cred = self.env['sii_connector.credential'].get_active()
        cert = cred.credential_id
        session = Session()
        session.cert = (cert.cert_file, cert.key_file)
        return Client(cred.endpoint, transport=Transport(session=session))

    @api.model
def fetch_rc_rv(self, month, year):
        client = self._get_client()
        rc = client.service.getRegistroRC(mes=month, ano=year)
        rv = client.service.getRegistroRV(mes=month, ano=year)
        return rc, rv

    @api.model
def _cron_generate_f29(self):
        today = fields.Date.today()
        month, year = today.month, today.year
        rc, rv = self.fetch_rc_rv(month, year)
        iva_debito = sum(item.MontoIva for item in rv)
        iva_credito = sum(item.MontoIva for item in rc)
        neto_iva = iva_debito - iva_credito
        self.env['flow_management.cashflow_line'].create({
            'date_start': today.replace(day=1),
            'amount': neto_iva,
            'category': 'tax',
            'name': f'F29 {year}-{month:02d}',
            'postponed': False,
        })
```

## 4. Data

### data/sii_menu.xml
```xml
<odoo>
  <menuitem id="menu_sii_root" name="SII Connector" sequence="20"/>
  <menuitem id="menu_sii_credentials" name="Credenciales SII" parent="menu_sii_root" action="action_sii_credentials"/>
  <record id="action_sii_credentials" model="ir.actions.act_window">
    <field name="name">Credenciales SII</field>
    <field name="res_model">sii_connector.credential</field>
    <field name="view_mode">tree,form</field>
  </record>
</odoo>
```

### data/ir_cron_sii.xml
```xml
<odoo>
  <record id="ir_cron_sii_f29" model="ir.cron">
    <field name="name">Generar F29 desde SII</field>
    <field name="model_id" ref="model_sii_connector_service"/>
    <field name="state">code</field>
    <field name="code">model._cron_generate_f29()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">months</field>
    <field name="active">True</field>
  </record>
</odoo>
```

## 5. Views de configuración

### views/sii_credential_views.xml
```xml
<odoo>
  <record id="view_sii_credential_tree" model="ir.ui.view">
    <field name="name">sii_connector.credential.tree</field>
    <field name="model">sii_connector.credential</field>
    <field name="arch" type="xml">
      <tree>
        <field name="name"/>
        <field name="endpoint"/>
        <field name="credential_id"/>
        <field name="active"/>
      </tree>
    </field>
  </record>

  <record id="view_sii_credential_form" model="ir.ui.view">
    <field name="name">sii_connector.credential.form</field>
    <field name="model">sii_connector.credential</field>
    <field name="arch" type="xml">
      <form>
        <sheet>
          <group>
            <field name="name"/>
            <field name="credential_id"/>
            <field name="endpoint"/>
            <field name="active"/>
          </group>
          <footer>
            <button name="_cron_generate_f29" string="Probar F29" type="object" class="btn-primary"/>
          </footer>
        </sheet>
      </form>
    </field>
  </record>
</odoo>
```

## 6. Seguridad
- `security/ir.model.access.csv` otorgando acceso a modelos `sii_connector.credential` y `sii_connector.service` solo al grupo **Administrador OFITEC**.

## 7. Tests básicos
*tests/test_sii_connector.py*:
```python
from odoo.tests.common import TransactionCase

class TestSiiConnector(TransactionCase):
    def test_fetch_rc_rv_keys(self):
        service = self.env['sii_connector.service']
        # Simular llamada con un endpoint de prueba
        # Asegurar que devuelve tuplas (rc, rv)
        rc, rv = service.fetch_rc_rv(1, 2025)
        self.assertTrue(isinstance(rc, list) and isinstance(rv, list))
```



## Actualización Plan de desarrollo modular
- **sii_connector**: Conexión con los servicios SOAP del SII para extraer registros de compras y ventas, construir reportes F29 y crear entradas de IVA en el flujo de caja.

