from odoo import models, fields, api


class SiteIncident(models.Model):
    _name = "ofitec.site.incident"
    _description = "Incidente en Obra"
    _order = "date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Título del Incidente", required=True)
    project_id = fields.Many2one(
        "project.project", string="Proyecto", required=True, index=True
    )
    date = fields.Date(string="Fecha", default=fields.Date.today, required=True)
    report_id = fields.Many2one("ofitec.daily.report", string="Reporte Diario Asociado")

    # Clasificación del incidente
    incident_type = fields.Selection(
        [
            ("safety", "Seguridad"),
            ("quality", "Calidad"),
            ("delay", "Retraso"),
            ("material", "Material"),
            ("equipment", "Equipo"),
            ("weather", "Clima"),
            ("other", "Otro"),
        ],
        string="Tipo de Incidente",
        required=True,
    )

    severity = fields.Selection(
        [
            ("low", "Bajo"),
            ("medium", "Medio"),
            ("high", "Alto"),
            ("critical", "Crítico"),
        ],
        string="Severidad",
        required=True,
        default="medium",
    )

    # Descripción y solución
    description = fields.Text(string="Descripción del Incidente", required=True)
    immediate_action = fields.Text(string="Acción Inmediata Tomada")
    preventive_action = fields.Text(string="Acción Preventiva")
    responsible_id = fields.Many2one("res.users", string="Responsable", required=True)
    deadline = fields.Date(string="Fecha Límite de Resolución")

    # Estado y seguimiento
    state = fields.Selection(
        [
            ("reported", "Reportado"),
            ("investigating", "En Investigación"),
            ("resolved", "Resuelto"),
            ("closed", "Cerrado"),
        ],
        string="Estado",
        default="reported",
        required=True,
        tracking=True,
    )

    # Metadata
    user_id = fields.Many2one(
        "res.users",
        string="Reportado por",
        default=lambda self: self.env.user,
        required=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )

    @api.model
    def create(self, vals):
        if not vals.get("name"):
            incident_type = dict(self._fields["incident_type"].selection).get(
                vals.get("incident_type"), "Incidente"
            )
            vals["name"] = f'{incident_type} - {vals.get("date", fields.Date.today())}'
        return super(SiteIncident, self).create(vals)

    def action_start_investigation(self):
        """Iniciar investigación del incidente"""
        self.write({"state": "investigating"})

    def action_resolve(self):
        """Marcar incidente como resuelto"""
        self.write({"state": "resolved"})

    def action_close(self):
        """Cerrar incidente"""
        self.write({"state": "closed"})

    def action_convert_to_risk(self):
        """Convertir incidente crítico en riesgo de proyecto"""
        self.ensure_one()
        if self.severity in ["high", "critical"]:
            risk_vals = {
                "name": f"Riesgo derivado de incidente: {self.name}",
                "project_id": self.project_id.id,
                "incident_id": self.id,
                "risk_category": self._get_risk_category_from_incident(),
                "severity": self.severity,
                "probability": self._calculate_risk_probability(),
                "description": f"Incidente convertido automáticamente a riesgo:\n\n{self.description}",
                "causes": f'Causa raíz del incidente: {self.immediate_action or "Por determinar"}',
                "responsible_id": self.responsible_id.id,
                "status": "identified",
            }
            risk = self.env["ofitec.project.risk"].create(risk_vals)
            return risk
        return False

    def _get_risk_category_from_incident(self):
        """Determinar categoría de riesgo basada en tipo de incidente"""
        category_mapping = {
            "safety": "safety",
            "quality": "quality",
            "delay": "schedule",
            "material": "procurement",
            "equipment": "technical",
            "weather": "environmental",
            "other": "operational",
        }
        return category_mapping.get(self.incident_type, "operational")

    def _calculate_risk_probability(self):
        """Calcular probabilidad de riesgo basada en severidad del incidente"""
        probability_mapping = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "very_high",
        }
        return probability_mapping.get(self.severity, "medium")

    @api.model
    def create_from_report(self, report_id, incident_data):
        """Crear incidente desde un reporte diario"""
        report = self.env["ofitec.daily.report"].browse(report_id)
        return self.create(
            {
                "project_id": report.project_id.id,
                "report_id": report.id,
                "date": report.date,
                "description": incident_data.get("description", ""),
                "incident_type": incident_data.get("type", "other"),
                "severity": incident_data.get("severity", "medium"),
                "user_id": report.user_id.id,
            }
        )
