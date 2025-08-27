from odoo import models, fields, api

class DailyReport(models.Model):
    _name = 'ofitec.daily.report'
    _description = 'Reporte Diario de Obra'

    name = fields.Char(string='Título', required=True)
    project_id = fields.Many2one('project.project', string='Proyecto', required=True)
    date = fields.Date(string='Fecha', default=fields.Date.today, required=True)
    progress = fields.Float(string='Progreso (%)', required=True)
    description = fields.Text(string='Descripción')
    user_id = fields.Many2one('res.users', string='Reportado por', default=lambda self: self.env.user)

    @api.model
    def create(self, vals):
        # Lógica adicional para validación con IA si es necesario
        return super(DailyReport, self).create(vals)
