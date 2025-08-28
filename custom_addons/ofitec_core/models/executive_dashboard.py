from odoo import models, fields, api
from datetime import datetime, timedelta


class ExecutiveDashboard(models.Model):
    _name = "ofitec.executive.dashboard"
    _description = "Dashboard Ejecutivo OFITEC.AI"
    _auto = False  # Vista de solo lectura

    # Campos calculados para KPIs
    total_projects = fields.Integer(
        string="Total de Proyectos", compute="_compute_totals"
    )
    active_projects = fields.Integer(
        string="Proyectos Activos", compute="_compute_totals"
    )
    completed_reports = fields.Integer(
        string="Reportes Completados (Mes)", compute="_compute_totals"
    )
    total_risks = fields.Integer(
        string="Total Riesgos Activos", compute="_compute_totals"
    )
    critical_risks = fields.Integer(
        string="Riesgos Críticos", compute="_compute_totals"
    )
    total_budget = fields.Monetary(
        string="Presupuesto Total", compute="_compute_financials"
    )
    total_cost = fields.Monetary(
        string="Costo Total Real", compute="_compute_financials"
    )
    avg_variance = fields.Float(
        string="Varianza Promedio (%)", compute="_compute_financials"
    )

    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )

    @api.model
    def _compute_totals(self):
        """Calcular métricas generales"""

        for record in self:
            # Proyectos
            record.total_projects = self.env["project.project"].search_count([])
            record.active_projects = self.env["project.project"].search_count(
                [("state", "not in", ["done", "cancelled"])]
            )

            # Reportes del mes
            start_of_month = datetime.now().replace(day=1)
            record.completed_reports = self.env["ofitec.daily.report"].search_count(
                [("state", "=", "approved"), ("date", ">=", start_of_month.date())]
            )

            # Riesgos
            record.total_risks = self.env["ofitec.project.risk"].search_count(
                [("status", "not in", ["closed", "occurred"])]
            )
            record.critical_risks = self.env["ofitec.project.risk"].search_count(
                [
                    ("severity", "=", "critical"),
                    ("status", "not in", ["closed", "occurred"]),
                ]
            )

    @api.model
    def _compute_financials(self):
        """Calcular métricas financieras"""

        for record in self:
            budgets = self.env["ofitec.project.financials"].search(
                [("state", "in", ["active", "approved"])]
            )

            if budgets:
                record.total_budget = sum(b.budget_amount for b in budgets)
                record.total_cost = sum(b.progress_cost for b in budgets)

                # Calcular varianza promedio ponderada
                total_weight = sum(b.budget_amount for b in budgets)
                if total_weight > 0:
                    weighted_variance = sum(
                        (b.variance_percentage * b.budget_amount) / total_weight
                        for b in budgets
                    )
                    record.avg_variance = weighted_variance
                else:
                    record.avg_variance = 0
            else:
                record.total_budget = 0
                record.total_cost = 0
                record.avg_variance = 0

    @api.model
    def get_dashboard_summary(self):
        """Obtener resumen completo del dashboard"""

        self._compute_totals()
        self._compute_financials()

        return {
            "projects": {"total": self.total_projects, "active": self.active_projects},
            "reports": {"completed_this_month": self.completed_reports},
            "risks": {
                "total_active": self.total_risks,
                "critical": self.critical_risks,
            },
            "financials": {
                "total_budget": self.total_budget,
                "total_cost": self.total_cost,
                "avg_variance": self.avg_variance,
            },
        }

    @api.model
    def get_recent_activity(self):
        """Obtener actividad reciente del sistema"""

        activities = []

        # Reportes recientes
        recent_reports = self.env["ofitec.daily.report"].search(
            [("state", "=", "approved")], order="date desc", limit=3
        )

        for report in recent_reports:
            activities.append(
                {
                    "type": "report",
                    "title": f"Reporte aprobado: {report.name}",
                    "description": f"Proyecto: {report.project_id.name} - Progreso: {report.progress}%",
                    "date": report.date,
                    "user": report.user_id.name,
                }
            )

        # Riesgos nuevos
        recent_risks = self.env["ofitec.project.risk"].search(
            [("identification_date", ">=", datetime.now().date() - timedelta(days=7))],
            order="identification_date desc",
            limit=2,
        )

        for risk in recent_risks:
            activities.append(
                {
                    "type": "risk",
                    "title": f"Nuevo riesgo: {risk.name}",
                    "description": f'Categoría: {dict(risk._fields["risk_category"].selection).get(risk.risk_category)}',
                    "date": risk.identification_date,
                    "user": risk.user_id.name,
                }
            )

        # Incidentes resueltos
        recent_incidents = self.env["ofitec.site.incident"].search(
            [
                ("state", "=", "resolved"),
                ("date", ">=", datetime.now().date() - timedelta(days=7)),
            ],
            order="date desc",
            limit=2,
        )

        for incident in recent_incidents:
            activities.append(
                {
                    "type": "incident",
                    "title": f"Incidente resuelto: {incident.name}",
                    "description": f'Tipo: {dict(incident._fields["incident_type"].selection).get(incident.incident_type)}',
                    "date": incident.date,
                    "user": incident.user_id.name,
                }
            )

        return sorted(activities, key=lambda x: x["date"], reverse=True)

    @api.model
    def get_alerts_and_warnings(self):
        """Obtener alertas y advertencias activas"""

        alerts = []

        # Riesgos críticos sin asignar
        unassigned_critical = self.env["ofitec.project.risk"].search_count(
            [
                ("severity", "=", "critical"),
                ("responsible_id", "=", False),
                ("status", "not in", ["closed", "occurred"]),
            ]
        )

        if unassigned_critical > 0:
            alerts.append(
                {
                    "level": "danger",
                    "title": "Riesgos críticos sin asignar",
                    "message": f"{unassigned_critical} riesgos críticos requieren asignación inmediata",
                    "action": "assign_responsible",
                }
            )

        # Varianza presupuestaria alta
        high_variance = self.env["ofitec.project.financials"].search_count(
            [("state", "in", ["active", "approved"]), ("variance_percentage", ">", 20)]
        )

        if high_variance > 0:
            alerts.append(
                {
                    "level": "warning",
                    "title": "Varianza presupuestaria alta",
                    "message": f"{high_variance} proyectos exceden el presupuesto en más del 20%",
                    "action": "review_budget",
                }
            )

        # Reportes pendientes de aprobación
        pending_reports = self.env["ofitec.daily.report"].search_count(
            [("state", "=", "submitted")]
        )

        if pending_reports > 0:
            alerts.append(
                {
                    "level": "info",
                    "title": "Reportes pendientes",
                    "message": f"{pending_reports} reportes diarios pendientes de aprobación",
                    "action": "approve_reports",
                }
            )

        # Incidentes sin resolver
        unresolved_incidents = self.env["ofitec.site.incident"].search_count(
            [("state", "not in", ["resolved", "closed"])]
        )

        if unresolved_incidents > 0:
            alerts.append(
                {
                    "level": "warning",
                    "title": "Incidentes sin resolver",
                    "message": f"{unresolved_incidents} incidentes requieren atención",
                    "action": "resolve_incidents",
                }
            )

        return alerts
