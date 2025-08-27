from odoo import models, fields, api

class ProjectBudget(models.Model):
    _name = 'ofitec.project.financials'
    _description = 'Presupuesto y Costos de Proyecto'

    name = fields.Char(string='Nombre', required=True)
    project_id = fields.Many2one('project.project', string='Proyecto', required=True)
    cost_rate = fields.Float(string='Tasa de Costo', required=True)
    progress_cost = fields.Float(string='Costo de Progreso', compute='_compute_progress_cost', store=True)
    budget_amount = fields.Float(string='Monto Presupuesto')

    @api.depends('cost_rate')
    def _compute_progress_cost(self):
        for record in self:
            # Calcular basado en reportes diarios
            reports = self.env['ofitec.daily.report'].search([('project_id', '=', record.project_id.id)])
            total_progress = sum(reports.mapped('progress'))
            record.progress_cost = total_progress * record.cost_rate / 100

    def update_costs_from_progress(self, project_id):
        reports = self.env['ofitec.daily.report'].search([('project_id', '=', project_id)])
        total_progress = sum(reports.mapped('progress'))
        self.write({'progress_cost': total_progress * self.cost_rate / 100})
