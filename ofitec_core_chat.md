# 🗂 Chat del módulo ofitec\_core

> **Objetivo:** Servir como núcleo del sistema, gestionando datos compartidos, endpoints centrales y modelos base para proyectos, usuarios extendidos y configuraciones globales.

## 1. Estructura del addon

```
ofitec_core/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── core_settings.py
│   ├── project_extension.py
│   └── user_profile.py
├── controllers/
│   └── main.py
├── data/
│   └── core_data.xml
├── security/
│   ├── ir.model.access.csv
│   └── core_security.xml
└── tests/
    └── test_core.py
```

## 2. **manifest**.py

```python
{
    'name': 'OFITEC Core',
    'version': '16.0.1.0.0',
    'category': 'Base',
    'summary': 'API central y modelos de datos compartidos',
    'depends': ['base', 'project', 'res_users'],
    'data': [
        'security/ir.model.access.csv',
        'security/core_security.xml',
        'data/core_data.xml',
    ],
    'installable': True,
    'application': False,
}
```

## 3. Modelos clave

### 3.1 core\_settings.py

```python
from odoo import models, fields

class CoreSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_project_type = fields.Selection([
        ('construction', 'Construcción'),
        ('infrastructure', 'Infraestructura')
    ], string='Tipo de Proyecto por defecto')

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'ofitec_core.default_project_type', self.default_project_type)

    def get_values(self):
        res = super().get_values()
        res['default_project_type'] = self.env['ir.config_parameter'].sudo().get_param(
            'ofitec_core.default_project_type')
        return res
```

### 3.2 project\_extension.py

```python
from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = 'project.project'

    subcontractor_id = fields.Many2one('subcontractor.management', string='Subcontratista Principal')
    manager_id       = fields.Many2one('res.users', string='Project Manager')
    risk_score       = fields.Float(string='Risk Score', default=0.0)
```

### 3.3 user\_profile.py

```python
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    phone_mobile  = fields.Char(string='Teléfono Móvil')
    emergency_contact = fields.Char(string='Contacto de Emergencia')
```

## 4. Controladores

### controllers/main.py

```python
from odoo import http
from odoo.http import request

class CoreController(http.Controller):

    @http.route('/ofitec/health', auth='public', type='json')
    def health_check(self):
        return {'status': 'ok', 'modules': request.env['ir.module.module'].
                sudo().search_read([('state','=','installed')], ['name', 'latest_version'])}
```

## 5. Data inicial

### data/core\_data.xml

```xml
<odoo>
  <record id="ofitec_core_default_project_type_construction" model="ir.config_parameter">
    <field name="key">ofitec_core.default_project_type</field>
    <field name="value">construction</field>
  </record>
</odoo>
```

## 6. Seguridad

- `ir.model.access.csv`: acceso a modelos core\_settings, project\_extension, user\_profile.
- `core_security.xml`: reglas para que solo administradores cambien `core_settings`.

## 7. Tests

- `tests/test_core.py`: validar inheritance de `project.project` y rutas de controller.

---

Con esto definimos el módulo **ofitec\_core**, que centraliza ajustes globales, extiende proyectos y usuarios, y expone rutas básicas para salud del sistema. Lo vinculamos a **ofitec\_theme** para estilo de páginas públicas si fuera necesario.

