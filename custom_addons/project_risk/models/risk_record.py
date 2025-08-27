from odoo import models, fields, api
from datetime import timedelta

class RiskRecord(models.Model):
    _name = 'ofitec.project.risk'
    _description = 'Registro de Riesgos de Proyecto'
    _order = 'create_date desc'

    name = fields.Char(string='Nombre del Riesgo', required=True)
    project_id = fields.Many2one('project.project', string='Proyecto', required=True, index=True)
    incident_id = fields.Many2one('ofitec.site.incident', string='Incidente Relacionado')

    # Clasificación del riesgo
    risk_category = fields.Selection([
        ('technical', 'Técnico'),
        ('financial', 'Financiero'),
        ('operational', 'Operacional'),
        ('environmental', 'Ambiental'),
        ('safety', 'Seguridad'),
        ('regulatory', 'Regulatorio'),
        ('market', 'Mercado'),
        ('other', 'Otro')
    ], string='Categoría', required=True)

    severity = fields.Selection([
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Crítico')
    ], string='Severidad', required=True, default='medium')

    probability = fields.Selection([
        ('very_low', 'Muy Baja (0-20%)'),
        ('low', 'Baja (21-40%)'),
        ('medium', 'Media (41-60%)'),
        ('high', 'Alta (61-80%)'),
        ('very_high', 'Muy Alta (81-100%)')
    ], string='Probabilidad', required=True, default='medium')

    # Evaluación cuantitativa
    probability_value = fields.Float(string='Probabilidad Numérica (%)', compute='_compute_probability_value', store=True)
    impact_value = fields.Monetary(string='Impacto Monetario', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    risk_exposure = fields.Monetary(string='Exposición al Riesgo', compute='_compute_risk_exposure', store=True, currency_field='currency_id')

    # Descripción y gestión
    description = fields.Text(string='Descripción del Riesgo', required=True)
    causes = fields.Text(string='Causas Potenciales')
    consequences = fields.Text(string='Consecuencias')
    mitigation_plan = fields.Text(string='Plan de Mitigación', required=True)
    contingency_plan = fields.Text(string='Plan de Contingencia')
    responsible_id = fields.Many2one('res.users', string='Responsable', required=True)
    deadline = fields.Date(string='Fecha Límite de Mitigación')

    # Estado y seguimiento
    status = fields.Selection([
        ('identified', 'Identificado'),
        ('analyzing', 'En Análisis'),
        ('mitigating', 'En Mitigación'),
        ('mitigated', 'Mitigado'),
        ('closed', 'Cerrado'),
        ('occurred', 'Ocurrido')
    ], string='Estado', default='identified', required=True, tracking=True)

    # Fechas importantes
    identification_date = fields.Date(string='Fecha de Identificación', default=fields.Date.today, required=True)
    mitigation_start_date = fields.Date(string='Inicio de Mitigación')
    mitigation_end_date = fields.Date(string='Fin de Mitigación')
    actual_occurrence_date = fields.Date(string='Fecha de Ocurrencia')

    # Seguimiento y métricas
    mitigation_progress = fields.Float(string='Progreso de Mitigación (%)', default=0)
    effectiveness_rating = fields.Selection([
        ('1', '1 - Muy Baja'),
        ('2', '2 - Baja'),
        ('3', '3 - Media'),
        ('4', '4 - Alta'),
        ('5', '5 - Muy Alta')
    ], string='Efectividad de Mitigación')

    # Metadata
    user_id = fields.Many2one('res.users', string='Creado por', default=lambda self: self.env.user, required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)

    @api.depends('probability')
    def _compute_probability_value(self):
        probability_map = {
            'very_low': 10,
            'low': 30,
            'medium': 50,
            'high': 70,
            'very_high': 90
        }
        for record in self:
            record.probability_value = probability_map.get(record.probability, 50)

    @api.depends('probability_value', 'impact_value')
    def _compute_risk_exposure(self):
        for record in self:
            record.risk_exposure = (record.probability_value / 100) * record.impact_value

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            category = dict(self._fields['risk_category'].selection).get(vals.get('risk_category'), 'Riesgo')
            vals['name'] = f'{category} - {vals.get("identification_date", fields.Date.today())}'
        return super(RiskRecord, self).create(vals)

    def action_start_analysis(self):
        """Iniciar análisis del riesgo"""
        self.write({'status': 'analyzing'})

    def action_start_mitigation(self):
        """Iniciar mitigación del riesgo"""
        self.write({
            'status': 'mitigating',
            'mitigation_start_date': fields.Date.today()
        })

    def action_complete_mitigation(self):
        """Completar mitigación del riesgo"""
        self.write({
            'status': 'mitigated',
            'mitigation_end_date': fields.Date.today()
        })

    def action_close_risk(self):
        """Cerrar riesgo"""
        self.write({'status': 'closed'})

    def action_risk_occurred(self):
        """Marcar que el riesgo ocurrió"""
        self.write({
            'status': 'occurred',
            'actual_occurrence_date': fields.Date.today()
        })

    @api.model
    def create_risk_from_incident(self, incident):
        """Crear riesgo desde un incidente"""
        return self.create({
            'name': f'Riesgo de {incident.name}',
            'project_id': incident.project_id.id,
            'incident_id': incident.id,
            'description': f'Riesgo derivado del incidente: {incident.description}',
            'risk_category': self._map_incident_to_risk_category(incident.incident_type),
            'severity': incident.severity,
            'probability': 'medium',
            'impact_value': 0,  # A determinar por el usuario
            'responsible_id': incident.responsible_id.id if incident.responsible_id else incident.user_id.id,
            'identification_date': incident.date
        })

    def _map_incident_to_risk_category(self, incident_type):
        """Mapear tipo de incidente a categoría de riesgo"""
        mapping = {
            'safety': 'safety',
            'quality': 'technical',
            'delay': 'operational',
            'material': 'financial',
            'equipment': 'technical',
            'weather': 'environmental'
        }
        return mapping.get(incident_type, 'other')

    @api.model
    def generate_risk_report(self, project_id):
        """Generar reporte de riesgos para un proyecto"""
        risks = self.search([('project_id', '=', project_id)])
        return {
            'total_risks': len(risks),
            'high_severity': len(risks.filtered(lambda r: r.severity in ['high', 'critical'])),
            'mitigated': len(risks.filtered(lambda r: r.status == 'mitigated')),
            'total_exposure': sum(risks.mapped('risk_exposure'))
        }
