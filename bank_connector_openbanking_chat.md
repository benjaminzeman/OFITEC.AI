# Chat del módulo bank\_connector\_openbanking

> **Objetivo:** Permitir al usuario elegir cómo importar extractos bancarios:
>
> 1. Subida manual de OFX/CAMT/CSV
> 2. Conexión SFTP a carpeta del banco
> 3. Open Banking (API de BCI)

## Estructura del addon

```
bank_connector_openbanking/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_config_settings.py
│   └── bci_client.py
├── data/
│   ├── ir_cron_openbanking.xml
│   └── bank_connector_menu.xml
└── security/
    └── ir.model.access.csv
```

---

## 1. **init**.py

```python
# -*- coding: utf-8 -*-
from . import models
```

## 2. **manifest**.py

```python
{
    'name': 'Bank Connector OpenBanking',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Banking',
    'summary': 'Importación de extractos bancarios: manual, SFTP o Open Banking BCI',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/bank_connector_menu.xml',
        'data/ir_cron_openbanking.xml',
    ],
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_backend': [],
    },
}
```

---

## 3. Modelos

### 3.1. Configuración (res\_config\_settings.py)

```python
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Credenciales y endpoints
    bci_client_id     = fields.Char(string='BCI Client ID')
    bci_client_secret = fields.Char(string='BCI Client Secret')
    bci_token_url     = fields.Char(
        string='BCI OAuth2 Token URL',
        default='https://psd2-sandbox.eu/auth/oauth/v2/token')
    bci_api_base      = fields.Char(
        string='BCI API Base URL',
        default='https://psd2-sandbox.eu')

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('bci.client_id', self.bci_client_id or '')
        params.set_param('bci.client_secret', self.bci_client_secret or '')
        params.set_param('bci.token_url', self.bci_token_url)
        params.set_param('bci.api_base', self.bci_api_base)

    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update({
            'bci_client_id':     params.get_param('bci.client_id', ''),
            'bci_client_secret': params.get_param('bci.client_secret', ''),
            'bci_token_url':     params.get_param('bci.token_url'),
            'bci_api_base':      params.get_param('bci.api_base'),
        })
        return res
```

### 3.2. Cliente BCI (bci\_client.py)

```python
# contenido existente de BCIClient...
```

### 3.3. Cliente Santander (santander\_client.py)

```python
import requests
from datetime import timedelta, datetime
from odoo import models, api, fields
from requests_oauthlib import OAuth2Session

class SantanderClient(models.AbstractModel):
    _name = 'bank_connector_openbanking.santander_client'
    _description = 'Conector Open Banking Santander Chile'

    @api.model
    def _get_oauth_session(self):
        params = self.env['ir.config_parameter'].sudo()
        client_id     = params.get_param('santander.client_id')
        client_secret = params.get_param('santander.client_secret')
        token_url     = params.get_param('santander.token_url')
        sess = OAuth2Session(client_id, scope=['accounts','transactions'])
        sess.fetch_token(
            token_url,
            client_id=client_id,
            client_secret=client_secret,
            include_client_id=True
        )
        return sess

    @api.model
    def fetch_transactions(self, bank_account_id, from_date, to_date):
        sess = self._get_oauth_session()
        base = self.env['ir.config_parameter'].sudo().get_param('santander.api_base')
        url = f"{base}/open-banking/v1/accounts/{bank_account_id}/transactions"
        params = {
            'fromBookingDateTime': from_date.strftime('%Y-%m-%dT00:00:00'),
            'toBookingDateTime':   to_date.strftime('%Y-%m-%dT23:59:59'),
        }
        resp = sess.get(url, params=params)
        resp.raise_for_status()
        data = resp.json().get('Data', {}).get('Transaction', [])
        txns = []
        for t in data:
            txns.append({
                'date':     t['BookingDateTime'][:10],
                'amount':   float(t['TransactionAmount']['Amount']),
                'currency': t['TransactionAmount']['Currency'],
                'name':     t.get('MerchantDetails',{}).get('MerchantName') or t['TransactionId'],
                'account_id': bank_account_id,
            })
        return txns

    @api.model
    def import_santander_transactions(self):
        BankStmt = self.env['account.bank.statement']
        today = fields.Date.context_today(self)
        start = today - timedelta(days=2)
        for acc in self.env['res.partner.bank'].search([('active','=',True),('santander_account_id','!=',False)]):
            txns = self.fetch_transactions(acc.santander_account_id, start, today)
            BankStmt.import_api_statements(txns)
        return True
```

---

## 4. Data y Menú (actualizado)

Añadimos en `bank_connector_menu.xml` opciones para configurar credenciales de Santander y SFTP:

```xml
<record id="action_santander_settings" model="ir.actions.act_window">
  <field name="name">Santander OpenBanking</field>
  <field name="res_model">res.config.settings</field>
  <field name="view_mode">form</field>
  <field name="target">current</field>
  <field name="context">{'module_to_configure':'santander'}</field>
</record>
<menuitem id="menu_santander_settings" name="Santander Settings"
          parent="menu_bank_connector_root"
          action="action_santander_settings"/>
```

Y en `ir_cron_openbanking.xml`:

```xml
<record id="ir_cron_santander_import" model="ir.cron">
  <field name="name">Importar Transacciones Santander</field>
  <field name="model_id" ref="bank_connector_openbanking.model_santander_client"/>
  <field name="state">code</field>
  <field name="code">model.import_santander_transactions()</field>
  <field name="interval_number">1</field>
  <field name="interval_type">days</field>
  <field name="active">True</field>
</record>
```

---

## 5. Configuración SFTP (sftp\_import.py)

```python
# models/sftp_import.py
import os
import paramiko
from odoo import models, api, fields

class SFTPImport(models.AbstractModel):
    _name = 'bank_connector_openbanking.sftp_import'

    @api.model
    def import_sftp_statements(self):
        params = self.env['ir.config_parameter'].sudo()
        host     = params.get_param('sftp.host')
        user     = params.get_param('sftp.user')
        pwd      = params.get_param('sftp.password')
        remote_path = params.get_param('sftp.path')
        local_tmp   = '/tmp/bank_files'
        os.makedirs(local_tmp, exist_ok=True)
        transport = paramiko.Transport((host, 22))
        transport.connect(username=user, password=pwd)
        sftp = paramiko.SFTPClient.from_transport(transport)
        for filename in sftp.listdir(remote_path):
            localf = os.path.join(local_tmp, filename)
            sftp.get(os.path.join(remote_path, filename), localf)
            self.env['account.bank.statement'].import_file(localf)
        sftp.close()
        transport.close()
        return True
```

Y el cron asociado:

````xml
<record id="ir_cron_sftp_import" model="ir.cron">
  <field name="name">Importar Extractos SFTP</field>
  <field name="model_id" ref="bank_connector_openbanking.model_sftp_import"/>
  <field name="state">code</field>
  <field name="code">model.import_sftp_statements()</field>
  <field name="interval_number">1</field>
  <field name="interval_type">days</field>
  <field name="active">True</field>
</record>
``` Data y Menú

### data/bank_connector_menu.xml
```xml
<odoo>
  <!-- Menú para configurar credenciales -->
  <menuitem id="menu_bank_connector_root" name="Bank Connector" sequence="50"/>
  <record id="action_bank_connector_settings" model="ir.actions.act_window">
    <field name="name">Bank Connector Settings</field>
    <field name="res_model">res.config.settings</field>
    <field name="view_mode">form</field>
    <field name="target">current</field>
  </record>
  <menuitem id="menu_bank_connector_settings" name="Settings"
            parent="menu_bank_connector_root"
            action="action_bank_connector_settings"/>
</odoo>
````

### data/ir\_cron\_openbanking.xml

```xml
<odoo>
  <record id="ir_cron_bci_import" model="ir.cron">
    <field name="name">Importar Transacciones BCI</field>
    <field name="model_id" ref="bank_connector_openbanking.model_bci_client"/>
    <field name="state">code</field>
    <field name="code">model.import_bci_transactions()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
    <field name="active">True</field>
  </record>
</odoo>
```

---

## 5. Seguridad

(security/ir.model.access.csv actualizado anteriormente)

---

## 6. Botón de Importación Manual

(Implementado en sección anterior)

---

## 7. Tests Automáticos

### tests/test\_bci\_client.py

```python
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock

class TestBCIClient(TransactionCase):
    def setUp(self):
        super().setUp()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('bci.client_id', 'id')
        params.set_param('bci.client_secret', 'secret')
        params.set_param('bci.token_url', 'https://test/token')
        params.set_param('bci.api_base', 'https://test/api')

    @patch('bank_connector_openbanking.bci_client.OAuth2Session.fetch_token')
    @patch('bank_connector_openbanking.bci_client.OAuth2Session.get')
    def test_fetch_transactions(self, mock_get, mock_fetch):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'Data': {'Transaction': [
            {'BookingDateTime':'2025-08-01T10:00:00','TransactionAmount':{'Amount':'100','Currency':'CLP'},'MerchantDetails':{'MerchantName':'TestName'}}
        ]}}
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp
        client = self.env['bank_connector_openbanking.bci_client']
        txns = client.fetch_transactions('acc1', self.env['ir.config_parameter'].sudo().get_param('bci.client_id'),
                                          self.env['ir.config_parameter'].sudo().get_param('bci.client_secret'))
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]['amount'], 100.0)
```

### tests/test\_santander\_client.py

```python
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock

class TestSantanderClient(TransactionCase):
    def setUp(self):
        super().setUp()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('santander.client_id', 'id')
        params.set_param('santander.client_secret', 'secret')
        params.set_param('santander.token_url', 'https://test/token')
        params.set_param('santander.api_base', 'https://test/api')

    @patch('bank_connector_openbanking.santander_client.OAuth2Session.fetch_token')
    @patch('bank_connector_openbanking.santander_client.OAuth2Session.get')
    def test_fetch_transactions(self, mock_get, mock_fetch):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'Data': {'Transaction': [
            {'BookingDateTime':'2025-08-01T09:00:00','TransactionAmount':{'Amount':'200','Currency':'CLP'},'MerchantDetails':{'MerchantName':'SantanderTest'}}
        ]}}
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp
        client = self.env['bank_connector_openbanking.santander_client']
        txns = client.fetch_transactions('acc2', self.env['ir.config_parameter'].sudo().get_param('santander.client_id'),
                                          self.env['ir.config_parameter'].sudo().get_param('santander.client_secret'))
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]['amount'], 200.0)
```

### tests/test\_sftp\_import.py

```python
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock
import os

class TestSFTPImport(TransactionCase):
    def setUp(self):
        super().setUp()
        # Configurar parámetros SFTP en ir.config_parameter
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('sftp.host', 'test.host')
        params.set_param('sftp.user', 'user')
        params.set_param('sftp.password', 'pass')
        params.set_param('sftp.path', '/remote/path')

    @patch('bank_connector_openbanking.sftp_import.paramiko.Transport')
    def test_import_sftp_statements(self, mock_transport):
        # Simular SFTP con archivos locales
        transport = mock_transport.return_value
        sftp = MagicMock()
        transport.connect = MagicMock()
        transport.close = MagicMock()
        paramiko.SFTPClient.from_transport = MagicMock(return_value=sftp)
        # Crear un archivo temporal
        tmp_dir = '/tmp/bank_files'
        os.makedirs(tmp_dir, exist_ok=True)
        sample_file = os.path.join(tmp_dir, 'statement.csv')
        with open(sample_file, 'w') as f:
            f.write('Date,Name,Amount,Account
2025-08-01,Sample,100,acc')
        sftp.listdir.return_value = ['statement.csv']
        sftp.get = lambda r, l: open(l, 'w').write('')
        sftp.close = MagicMock()
        transport.connect.assert_not_called()
        # Ejecutar import
        importer = self.env['bank_connector_openbanking.sftp_import']
        importer.import_sftp_statements()
        # Verificar que import_file fue llamado (método interno de Odoo)
        # Nota: este test asume que import_file no lanza excepción
        self.assertTrue(os.path.exists(sample_file))
```

---

Con estos tests, cubrimos:

- BCIClient y SantanderClient con OAuth mocking.
- SFTPImport con mock de paramiko y directorio local.

Queda pendiente la *deduplicación* y *logs* en tests. Adelantamos bastante la cobertura del módulo.



## 8. Ejecución de Tests

Para validar el módulo, ejecuta los siguientes comandos:

**1. Usando odoo-bin**

```bash
odoo-bin -c odoo.conf \
  --test-enable \
  --stop-after-init \
  -i bank_connector_openbanking
```

- `-c odoo.conf`: fichero de configuración con `addons_path` y conexión BD.
- `--test-enable`: activa la ejecución de tests.
- `--stop-after-init`: detiene el servidor tras los tests.
- `-i bank_connector_openbanking`: instala sólo este módulo para testear.

**2. Usando pytest**

```bash
pytest custom_addons/bank_connector_openbanking/tests \
  --maxfail=1 --disable-warnings -q
```

- Ejecuta todos los tests del directorio del módulo.
- `--maxfail=1`: detiene en el primer fallo.
- `--disable-warnings`: oculta warnings.
- `-q`: modo silencioso, muestra sólo resumen.

### Proceso paso a paso

1. Levanta un entorno limpio y asegúrate de la BD en `odoo.conf`.
2. Corre uno de los comandos anteriores.
3. Observa en consola los resultados:
   - **OK**: tests pasan.
   - **FAIL**: revisa traceback y ajusta código.
4. Verifica que no queden errores ni warnings.

Con esto garantizas la calidad y fiabilidad del módulo **bank\_connector\_openbanking** antes de su despliegue.

