from odoo import models, fields


class OfitecVisual(models.Model):
    _name = "ofitec.visual"
    _description = "OFITEC Visual Element"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)

