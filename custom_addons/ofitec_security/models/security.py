from odoo import models, fields, api

class OfitecSecurity(models.Model):
    _name = 'ofitec.security'
    _description = 'Configuración de Seguridad Avanzada'

    name = fields.Char(string='Nombre de la Regla', required=True)
    model_id = fields.Many2one('ir.model', string='Modelo', required=True)
    group_ids = fields.Many2many('res.groups', string='Grupos Permitidos')
    domain = fields.Char(string='Dominio de Filtro', help='Dominio adicional para restringir acceso')
    active = fields.Boolean(default=True, string='Activo')

    @api.model
    def check_access(self, model_name, operation, record_ids=None):
        """Verificar acceso basado en reglas de seguridad"""
        rules = self.search([
            ('model_id.model', '=', model_name),
            ('active', '=', True)
        ])

        if not rules:
            return True  # No hay reglas específicas, permitir

        user_groups = self.env.user.groups_id
        for rule in rules:
            if rule.group_ids & user_groups:
                return True

        return False
