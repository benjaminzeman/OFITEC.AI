# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Campos adicionales para gestión avanzada de proyectos
    project_complexity = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica')
    ], string='Complejidad del Proyecto', default='medium')

    estimated_budget = fields.Float(string='Presupuesto Estimado')
    actual_budget = fields.Float(string='Presupuesto Real')
    budget_variance = fields.Float(string='Varianza Presupuestaria', compute='_compute_budget_variance')

    @api.depends('estimated_budget', 'actual_budget')
    def _compute_budget_variance(self):
        for record in self:
            if record.estimated_budget:
                record.budget_variance = ((record.actual_budget - record.estimated_budget) / record.estimated_budget) * 100
            else:
                record.budget_variance = 0.0
