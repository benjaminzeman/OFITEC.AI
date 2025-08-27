from odoo import models, fields, api

class OfitecCore(models.Model):
    _name = 'ofitec.core'
    _description = 'Modelo base de OFITEC'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    active = fields.Boolean(default=True, string='Activo')

    # Aquí se pueden agregar campos y métodos comunes para todos los módulos
