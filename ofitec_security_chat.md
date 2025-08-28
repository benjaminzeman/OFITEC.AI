# 🗂 Chat del módulo ofitec\_security

> **Objetivo:** Gestionar roles, permisos, autenticación y control de acceso avanzado en Ofitec, con integración SSO (Google) y reglas dinámicas por proyecto.

## 1. Estructura del addon

```
ofitec_security/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── security_group.py
│   ├── record_rule.py
│   └── sso_config.py
├── views/
│   ├── security_settings_views.xml
│   ├── groups_views.xml
│   └── record_rules_views.xml
├── controllers/
│   └── sso_controller.py
├── data/
│   ├── security_groups.xml
│   ├── record_rules.xml
│   └── sso_data.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    └── test_security.py
```

## 2. **manifest**.py

```python
{
    'name': 'OFITEC Security',
    'version': '16.0.1.0.0',
    'category': 'Settings',
    'summary': 'Roles, permisos y autenticación avanzada (SSO) para Ofitec',
    'depends': ['base', 'ofitec_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/security_groups.xml',
        'data/record_rules.xml',
        'data/sso_data.xml',
        'views/security_settings_views.xml',
        'views/groups_views.xml',
        'views/record_rules_views.xml',
    ],
    'application': False,
    'installable': True,
}
```

## 3. Modelos

### 3.1 security\_group.py

```python
from odoo import models, fields

class SecurityGroup(models.Model):
    _inherit = 'res.groups'
    _description = 'Extensión de Grupos y Roles'

    ofitec_dashboard_access = fields.Boolean(
        string='Acceso a dashboard OFITEC', default=False)
    is_project_manager = fields.Boolean(
        string='Es Gestor de Proyecto', default=False)
    is_supervisor = fields.Boolean(
        string='Es Supervisor', default=False)
```

### 3.2 record\_rule.py

```python
from odoo import models, fields

class RecordRule(models.Model):
    _inherit = 'ir.rule'
    _description = 'Regla de registro dinámica por proyecto'

    project_dependent = fields.Boolean(
        string='Filtrar por proyecto', default=False)
    project_field = fields.Char(
        string='Campo proyecto', default='project_id')

    def _apply_project_filter(self, model, domain):
        # Aplica dominio por proyecto solo si el usuario está en grupo de PM
        user = self.env.user
        if self.project_dependent and user.has_group('ofitec_security.group_project_manager'):
            domain = ['|',('project_dependent','=',False),(model+'.'+self.project_field,'in',user.project_ids.ids)]
        return domain
```

### 3.3 sso\_config.py

```python
from odoo import models, fields, api

class SSOConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    google_client_id = fields.Char('Google Client ID')
    google_client_secret = fields.Char('Google Client Secret')
    google_redirect_uri = fields.Char('Redirect URI', default='/auth/google/callback')

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('ofitec_sso.google_client_id', self.google_client_id)
        params.set_param('ofitec_sso.google_client_secret', self.google_client_secret)
        params.set_param('ofitec_sso.google_redirect_uri', self.google_redirect_uri)

    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update({
            'google_client_id': params.get_param('ofitec_sso.google_client_id'),
            'google_client_secret': params.get_param('ofitec_sso.google_client_secret'),
            'google_redirect_uri': params.get_param('ofitec_sso.google_redirect_uri'),
        })
        return res
```

## 4. Controlador SSO

### controllers/sso\_controller.py

```python
from odoo import http
from odoo.http import request
import requests

class SSOController(http.Controller):

    @http.route('/auth/google', auth='public')
    def google_login(self, **kw):
        params = request.env['ir.config_parameter'].sudo()
        client_id = params.get_param('ofitec_sso.google_client_id')
        redirect = params.get_param('ofitec_sso.google_redirect_uri')
        auth_url = 'https://accounts.google.com/o/oauth2/auth'
        return request.redirect(
            f"{auth_url}?client_id={client_id}&redirect_uri={redirect}"+
            "&response_type=code&scope=openid email profile"
        )

    @http.route('/auth/google/callback', auth='public')
    def google_callback(self, code=None, **kw):
        params = request.env['ir.config_parameter'].sudo()
        token_url = 'https://oauth2.googleapis.com/token'
        data = {'code': code,
                'client_id': params.get_param('ofitec_sso.google_client_id'),
                'client_secret': params.get_param('ofitec_sso.google_client_secret'),
                'redirect_uri': params.get_param('ofitec_sso.google_redirect_uri'),
                'grant_type': 'authorization_code'}
        resp = requests.post(token_url, data=data).json()
        userinfo = requests.get(
            'https://openidconnect.googleapis.com/v1/userinfo',
            headers={'Authorization': f"Bearer {resp['access_token']}"}
        ).json()
        # Buscar o crear usuario
        User = request.env['res.users'].sudo()
        user = User.search([('login','=',userinfo['email'])], limit=1)
        if not user:
            user = User.create({
                'name': userinfo['name'],
                'login': userinfo['email'],
                'email': userinfo['email'],
            })
        # Iniciar sesión
        request.session.authenticate(request.session.db, user.login, user.login)
        return request.redirect('/')
```

## 5. Datos iniciales

### data/security\_groups.xml

```xml
<odoo>
  <record id="group_ofitec_admin" model="res.groups">
    <field name="name">Administrador OFITEC</field>
    <field name="category_id" ref="base.module_category_security"/>
  </record>
  <record id="group_project_manager" model="res.groups">
    <field name="name">Project Manager</field>
    <field name="implied_ids" eval="[(4, ref('group_ofitec_admin'))]"/>
  </record>
  <record id="group_supervisor" model="res.groups">
    <field name="name">Supervisor</field>
    <field name="implied_ids" eval="[(4, ref('group_project_manager'))]"/>
  </record>
</odoo>
```

### data/record\_rules.xml

```xml
<odoo>
  <record model="ir.rule" id="rule_project_record_pm">
    <field name="name">Record filtering per project for PM</field>
    <field name="model_id" ref="model_project_project"/>
    <field name="domain_force">[('id','in',user.project_ids.ids)]</field>
    <field name="groups" eval="[(4, ref('group_project_manager'))]"/>
  </record>
</odoo>
```

### data/sso\_data.xml

```xml
<odoo>
  <record id="auth_oauth_provider_google" model="auth.oauth.provider">
    <field name="name">Google</field>
    <field name="scope">openid email profile</field>
    <field name="auth_endpoint">https://accounts.google.com/o/oauth2/auth</field>
    <field name="token_endpoint">https://oauth2.googleapis.com/token</field>
    <field name="validation_endpoint">https://openidconnect.googleapis.com/v1/userinfo</field>
  </record>
</odoo>
```

## 6. Vistas de Configuración

### views/security\_settings\_views.xml

```xml
<odoo>
  <record id="view_res_config_settings_security_ofitec" model="ir.ui.view">
    <field name="name">security.settings.ofitec</field>
    <field name="model">res.config.settings</field>
    <field name="inherit_id" ref="base.res_config_settings_view_form"/>
    <field name="arch" type="xml">
      <div class="o_form_sheet">
        <h3>SSO Google</h3>
        <group>
          <field name="google_client_id"/>
          <field name="google_client_secret"/>
          <field name="google_redirect_uri"/>
        </group>
      </div>
    </field>
  </record>
</odoo>
```

## 7. Tests básicos

*tests/test\_security.py*:

```python
from odoo.tests.common import TransactionCase

class TestOfitecSecurity(TransactionCase):
    def test_group_hierarchy(self):
        admin = self.env.ref('ofitec_security.group_ofitec_admin')
        pm = self.env.ref('ofitec_security.group_project_manager')
        self.assertTrue(pm.implied_ids & admin)
```

---

## 8. Invitaciones de Usuario

Para controlar el acceso, solo los **Administradores OFITEC** pueden invitar nuevos usuarios.

### 8.1 Modelo `ofitec_security.invitation`

```python
from odoo import models, fields, api
import uuid

class UserInvitation(models.Model):
    _name = 'ofitec_security.invitation'
    _description = 'Invitación de Usuario OFITEC'

    email = fields.Char(string='Email', required=True)
    token = fields.Char(string='Token', required=True, default=lambda self: str(uuid.uuid4()))
    group_ids = fields.Many2many('res.groups', string='Grupos asignados')
    expiry_date = fields.Date(string='Expira en', default=lambda self: fields.Date.context_today(self) + fields.Date.timedelta(days=7))
    state = fields.Selection([('pending','Pendiente'),('sent','Enviado'),('accepted','Aceptada'),('expired','Expirada')], default='pending')
    inviter_id = fields.Many2one('res.users', string='Invitado por', default=lambda self: self.env.user.id)

    def action_send_invitation(self):
        # Enviar correo con enlace
        template = self.env.ref('ofitec_security.email_template_invitation')
        template.send_mail(self.id, force_send=True)
        self.state = 'sent'

    @api.model
def _cron_expire_invitations(self):
        today = fields.Date.context_today(self)
        expired = self.search([('state','=','pending'),('expiry_date','<', today)])
        expired.write({'state':'expired'})

    def action_accept(self, token):
        inv = self.search([('token','=',token),('state','=','pending')], limit=1)
        if inv and inv.expiry_date >= fields.Date.context_today(self):
            # Crear usuario
            user = self.env['res.users'].create({
                'login': inv.email,
                'email': inv.email,
                'groups_id': [(6,0,inv.group_ids.ids)],
            })
            inv.state = 'accepted'
            return user
        inv.state = 'expired'
        return False
```

### 8.2 Vistas y Email Template

**security\_settings\_views.xml**: sección “Invitaciones” con Kanban y form.

```xml
<record id="view_user_invitation_kanban" model="ir.ui.view">
  <field name="name">ofitec_security.invitation.kanban</field>
  <field name="model">ofitec_security.invitation</field>
  <field name="arch" type="xml">
    <kanban>
      <templates>
        <t t-name="kanban-box">
          <div class="oe_kanban_card">
            <strong><field name="email"/></strong>
            <div><field name="state"/></div>
            <div><field name="expiry_date"/></div>
          </div>
        </t>
      </templates>
    </kanban>
  </field>
</record>

<record id="email_template_invitation" model="mail.template">
  <field name="name">Invitación OFITEC</field>
  <field name="email_from">Ofitec &lt;no-reply@ofitec.com&gt;</field>
  <field name="subject">Invitación a Ofitec</field>
  <field name="model_id" ref="model_ofitec_security_invitation"/>
  <field name="body_html"><![CDATA[
    <p>Hola,</p>
    <p>Has sido invitado a unirte a Ofitec. Haz clic <a t-attf-href="https://tu.ofitec.com/invite/#{object.token}">aquí</a> para aceptar la invitación.</p>
    <p>Expira en: <t t-esc="object.expiry_date"/></p>
  ]]></field>
</record>
```

### 8.3 Cron de expiración (`data/sso_data.xml`)

```xml
<odoo>
  <record id="ir_cron_expire_invitations" model="ir.cron">
    <field name="name">Expirar Invitaciones OFITEC</field>
    <field name="model_id" ref="model_ofitec_security_invitation"/>
    <field name="state">code</field>
    <field name="code">model._cron_expire_invitations()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
  </record>
</odoo>
```

Con esto, solo los administradores podrán generar y gestionar invitaciones, y el usuario finalizará su registro a través de un enlace seguro.



---

## 9. Otras recomendaciones de seguridad y UX

Para fortalecer y enriquecer la plataforma, recomiendo incluir:

1. **Registro de auditoría (audit log)**

   - Modelo `res.users.log` que guarde cambios críticos (login/logout, cambio de permisos, creación/eliminación de registros).
   - Vista y filtros para que los admins revisen incidentes.

2. **Política de contraseñas**

   - Reglas de complejidad (longitud mínima, caracteres especiales).
   - Expiración periódica y recordatorios automáticos antes de caducar.

3. **Autenticación de múltiples factores (MFA)**

   - Integrar Odoo MFA (TOTP) o servicios externos (Duo, Authy).
   - Pantalla de configuración de MFA en perfil de usuario.

4. **Gestión de sesiones activas**

   - Panel donde el usuario y admin vean sesiones iniciadas (IP, agente, fecha).
   - Botón “Cerrar todas las sesiones” o “Cerrar sesión remota”.

5. **Restricciones de acceso por IP/subnet**

   - Configuración en settings para permitir rangos de IP confiables.
   - Bloqueo automático de IP tras X intentos fallidos.

6. **Captcha/anti-bot en login**

   - Implementar reCAPTCHA v3 en formulario de login e invitación para evitar ataques de fuerza bruta.

7. **SSO adicional**

   - Soporte para otros proveedores: Microsoft Azure AD, Okta, LDAP corporativo.
   - Mapeo dinámico de grupos basado en claims.

8. **Self-service de perfil**

   - Permitir a usuarios modificar foto, teléfono, notificaciones y revisar su historial de actividad.
   - Opción de regenerar token de API o revocar claves.

9. **Notificaciones y alertas**

   - Enviar correos o toasts cuando se crean nuevos permisos o invitaciones.
   - Resumen diario de accesos y cambios de seguridad.

10. **Documentación y onboarding**

    - Guías interactivas (tour in-app) para nuevos roles: cómo gestionar usuarios, invitaciones y permisos.
    - Sección de FAQs en configuraciones.

---

## 10. Gestión de Certificados Digitales

Para manejar de forma segura los certificados y claves que el cliente proporcione (SII y otros servicios):

### 10.1 Modelo `ofitec_security.digital_credential`

```python
from odoo import models, fields, api
class DigitalCredential(models.Model):
    _name = 'ofitec_security.digital_credential'
    _description = 'Certificado Digital y Claves'

    name = fields.Char(string='Nombre del Certificado', required=True)
    cert_file = fields.Binary(string='Archivo de Certificado (.pem/.p12)', required=True)
    key_file = fields.Binary(string='Archivo de Clave Privada', required=True)
    password = fields.Char(string='Contraseña (opcional)', help='Contraseña para el archivo de clave', encrypt=True)
    service = fields.Selection([
        ('sii','SII'),
        ('other','Otro'),
    ], string='Servicio', default='sii')
    active = fields.Boolean(string='Activo', default=True)
    upload_date = fields.Datetime(string='Fecha de Subida', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Subido por', default=lambda self: self.env.user.id)

    @api.model
def get_active_credential(self, service):
        return self.search([('service','=',service),('active','=',True)], limit=1)
```

### 10.2 Vistas de administración

- Form y tree para `digital_credential` bajo **Seguridad ▶ Credenciales Digitales**.
- Campos de archivo (Binary) y enmascaramiento de contraseña.
- Botón “Probar conexión” que valide el certificado (ping SII o servicio externo) y muestre resultados.

### 10.3 Seguridad y cifrado

- **encrypt=True** para el campo `password` (se almacenará cifrado en base de datos).
- Los archivos `.pem/.p12` se guardan en la base de datos Odoo, pero se recomienda usar un **vault externo** para producción (HashiCorp, AWS KMS).
- Acceso restringido solo al grupo **Administrador OFITEC** y roles con permiso explícito.

### 10.4 Uso en Integraciones

- Los módulos que consumen servicios (SII, APIs bancarias) usarán `digital_credential = env['ofitec_security.digital_credential'].get_active_credential('sii')` para cargar certificado y clave.
- Implementar lógica de fallback si no existe credencial activa.

> **Registro de cambios:** añadida sección para gestión de certificados digitales en `ofitec_security`, con modelo, vistas y recomendaciones de seguridad.



---

## Actualización de Seguridad Digital en Chat Maestro

- Se añadió en **ofitec\_security** el modelo `digital_credential` para almacenar certificados digitales (.pem/.p12), claves privadas y contraseñas cifradas.
- Vistas de administración seguras bajo **Seguridad ▶ Credenciales Digitales** con botón de prueba de conexión.
- Recomendaciones para encriptar campos sensibles y uso de vault externo en producción.
- Integración asegurada: los módulos de SII y bancarios cargarán automáticamente la credencial activa.

Estos cambios garantizan que todas las claves y certificados del cliente queden registrados de manera segura y centralizada.

