from odoo import http
from odoo.http import request
import json
from datetime import datetime, timedelta


class ExecutiveDashboardController(http.Controller):

    @http.route("/ofitec/dashboard/data", type="json", auth="user")
    def get_dashboard_data(self):
        """Obtener datos en tiempo real para el dashboard ejecutivo"""

        # Obtener proyecto activo (puedes modificar para múltiples proyectos)
        project_id = request.params.get("project_id", False)

        data = {
            "kpis": self._get_kpi_data(project_id),
            "risks": self._get_risk_data(project_id),
            "financials": self._get_financial_data(project_id),
            "reports": self._get_recent_reports(project_id),
            "alerts": self._get_active_alerts(project_id),
        }

        return data

    def _get_kpi_data(self, project_id):
        """Obtener KPIs principales"""

        # Progreso general del proyecto
        if project_id:
            project = request.env["project.project"].browse(project_id)
            progress = project.progress if project else 0
        else:
            # Promedio de todos los proyectos
            projects = request.env["project.project"].search([])
            progress = (
                sum(p.progress for p in projects) / len(projects) if projects else 0
            )

        # Reportes aprobados en el mes actual
        start_of_month = datetime.now().replace(day=1)
        reports_count = request.env["ofitec.daily.report"].search_count(
            [("state", "=", "approved"), ("date", ">=", start_of_month.date())]
        )

        # Riesgos críticos activos
        critical_risks = request.env["ofitec.project.risk"].search_count(
            [
                ("severity", "=", "critical"),
                ("status", "not in", ["closed", "occurred"]),
            ]
        )

        # Varianza promedio (ponderada por presupuesto)
        budgets = request.env["ofitec.project.financials"].search(
            [("state", "in", ["active", "approved"])]
            + ([("project_id", "=", project_id)] if project_id else [])
        )

        if budgets:
            total_budget = sum(b.budget_amount or 0 for b in budgets)
            if total_budget:
                weighted = (
                    sum(
                        ((b.variance_percentage or 0) * (b.budget_amount or 0))
                        for b in budgets
                    )
                    / total_budget
                )
            else:
                weighted = sum((b.variance_percentage or 0) for b in budgets) / len(
                    budgets
                )
            avg_variance = round(float(weighted), 2)
        else:
            avg_variance = 0.0

        return {
            "progress": round(progress, 1),
            "reports_this_month": reports_count,
            "critical_risks": critical_risks,
            "avg_variance": avg_variance,
        }

    def _get_risk_data(self, project_id):
        """Obtener datos de riesgos"""

        domain = [("status", "not in", ["closed", "occurred"])]
        if project_id:
            domain.append(("project_id", "=", project_id))

        risks = request.env["ofitec.project.risk"].search(domain)

        # Riesgos por categoría
        categories = {}
        total_exposure = 0
        critical_count = 0

        for risk in risks:
            cat = risk.risk_category
            categories[cat] = categories.get(cat, 0) + 1
            total_exposure += risk.risk_exposure
            if risk.severity == "critical":
                critical_count += 1

        return {
            "by_category": categories,
            "total_exposure": total_exposure,
            "critical_count": critical_count,
            "total_active": len(risks),
        }

    def _get_financial_data(self, project_id):
        """Obtener datos financieros"""

        domain = [("state", "in", ["active", "approved"])]
        if project_id:
            domain.append(("project_id", "=", project_id))

        budgets = request.env["ofitec.project.financials"].search(domain)

        if budgets:
            budget = budgets[0]  # Tomar el primer presupuesto activo
            return {
                "budget_amount": budget.budget_amount,
                "progress_cost": budget.progress_cost,
                "estimated_total_cost": budget.estimated_total_cost,
                "variance_amount": budget.variance_amount,
                "variance_percentage": budget.variance_percentage,
            }

        return {
            "budget_amount": 0,
            "progress_cost": 0,
            "estimated_total_cost": 0,
            "variance_amount": 0,
            "variance_percentage": 0,
        }

    def _get_recent_reports(self, project_id):
        """Obtener reportes recientes"""

        domain = [("state", "=", "approved")]
        if project_id:
            domain.append(("project_id", "=", project_id))

        reports = request.env["ofitec.daily.report"].search(
            domain, order="date desc", limit=5
        )

        return [
            {
                "id": r.id,
                "name": r.name,
                "date": r.date.strftime("%Y-%m-%d"),
                "progress": r.progress,
                "user": r.user_id.name,
            }
            for r in reports
        ]

    def _get_active_alerts(self, project_id):
        """Obtener alertas activas"""

        alerts = []

        # Verificar riesgos críticos
        critical_risks = request.env["ofitec.project.risk"].search_count(
            [
                ("severity", "=", "critical"),
                ("status", "not in", ["closed", "occurred"]),
            ]
        )

        if critical_risks > 0:
            alerts.append(
                {
                    "type": "danger",
                    "message": f"{critical_risks} riesgos críticos requieren atención inmediata",
                }
            )

        # Verificar varianza presupuestaria
        budgets = request.env["ofitec.project.financials"].search(
            [("state", "in", ["active", "approved"]), ("variance_percentage", ">", 15)]
        )

        if budgets:
            alerts.append(
                {
                    "type": "warning",
                    "message": f"Varianza presupuestaria alta en {len(budgets)} proyectos",
                }
            )

        # Verificar reportes pendientes
        pending_reports = request.env["ofitec.daily.report"].search_count(
            [("state", "=", "submitted")]
        )

        if pending_reports > 0:
            alerts.append(
                {
                    "type": "info",
                    "message": f"{pending_reports} reportes diarios pendientes de aprobación",
                }
            )

        return alerts

    @http.route("/ofitec/dashboard/chart/risks", type="json", auth="user")
    def get_risks_chart_data(self):
        """Datos para gráfico de riesgos por categoría"""

        risks = request.env["ofitec.project.risk"].search(
            [("status", "not in", ["closed", "occurred"])]
        )

        categories = {}
        for risk in risks:
            cat = dict(risk._fields["risk_category"].selection).get(
                risk.risk_category, "Otro"
            )
            categories[cat] = categories.get(cat, 0) + 1

        return {"labels": list(categories.keys()), "data": list(categories.values())}

    @http.route("/ofitec/dashboard/chart/costs", type="json", auth="user")
    def get_costs_chart_data(self):
        """Datos para gráfico de tendencia de costos"""

        # Obtener datos de los últimos 6 meses
        months = []
        budget_data = []
        actual_data = []

        for i in range(5, -1, -1):
            date = datetime.now() - timedelta(days=i * 30)
            months.append(date.strftime("%b %Y"))

            # Aquí iría la lógica para obtener costos históricos
            # Por ahora, datos simulados
            budget_data.append(100000 + i * 5000)
            actual_data.append(95000 + i * 6000)

        return {
            "labels": months,
            "datasets": [
                {"label": "Presupuesto", "data": budget_data},
                {"label": "Costo Real", "data": actual_data},
            ],
        }
