from odoo import models, fields, api

class AIBridge(models.Model):
    _name = 'ai.bridge'
    _description = 'Motor de IA para predicciones'

    name = fields.Char(string='Nombre', required=True)
    model_type = fields.Selection([
        ('cost_prediction', 'Predicción de Costos'),
        ('risk_analysis', 'Análisis de Riesgos'),
        ('sentiment', 'Análisis de Sentimiento')
    ], string='Tipo de Modelo', required=True)

    def predict_costs(self, project):
        # Lógica de predicción de costos con IA
        # Placeholder
        return {'predicted_cost': 100000, 'confidence': 0.85}

    def analyze_risk(self, project):
        # Análisis de riesgos
        risks = self.env['ofitec.project.risk'].search([('project_id', '=', project.id)])
        return {'risk_count': len(risks), 'high_risks': len(risks.filtered(lambda r: r.severity == 'high'))}

    def analyze_sentiment(self, message):
        # Análisis de sentimiento
        # Placeholder con Transformers
        if 'retraso' in message.lower() or 'problema' in message.lower():
            return 'negative'
        return 'neutral'
