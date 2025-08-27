from odoo import models, fields, api

class RiskRecord(models.Model):
    _name = 'ofitec.project.risk'
    _description = 'Registro de Riesgos de Proyecto'

    name = fields.Char(string='Nombre del Riesgo', required=True)
    project_id = fields.Many2one('project.project', string='Proyecto', required=True)
    description = fields.Text(string='Descripción', required=True)
    severity = fields.Selection([
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto')
    ], string='Severidad', default='medium', required=True)
    probability = fields.Float(string='Probabilidad (%)', required=True)
    impact = fields.Float(string='Impacto', required=True)
    mitigation_plan = fields.Text(string='Plan de Mitigación')
    status = fields.Selection([
        ('open', 'Abierto'),
        ('mitigated', 'Mitigado'),
        ('closed', 'Cerrado')
    ], string='Estado', default='open', required=True)

    @api.model
    def create_risk_from_incident(self, incident):
        return self.create({
            'name': incident.name,
            'project_id': incident.project_id.id,
            'description': f'Riesgo derivado de incidente: {incident.description}',
            'severity': 'medium'
        })
