from odoo import models, fields
from datetime import date
import calendar


class ProjectBudgetTrend(models.Model):
    _inherit = "ofitec.project.financials"

    def get_cost_trend_data(self):
        """Datos para el gráfico del Dashboard Ejecutivo (12 meses)."""
        self.ensure_one()

        today = fields.Date.context_today(self)
        # 12 meses recientes
        base = date(today.year, today.month, 1)
        months = []
        for i in range(11, -1, -1):
            y = base.year + (base.month - 1 - i) // 12
            m = (base.month - 1 - i) % 12 + 1
            months.append(date(y, m, 1))

        labels = [calendar.month_abbr[m.month] for m in months]

        cumulative = 0.0
        real_series = []
        for start in months:
            _, last_day = calendar.monthrange(start.year, start.month)
            end = date(start.year, start.month, last_day)
            reports = self.env["ofitec.daily.report"].search(
                [
                    ("project_id", "=", self.project_id.id),
                    ("state", "=", "approved"),
                    ("date", ">=", start),
                    ("date", "<=", end),
                ]
            )
            month_cost = 0.0
            for r in reports:
                labor = (r.hours_worked or 0.0) * (self.cost_rate or 0.0)
                materials = (
                    labor * ((self.material_cost_rate or 0.0) / 100.0)
                    if self.material_cost_rate
                    else 0.0
                )
                equipment = (
                    labor * ((self.equipment_cost_rate or 0.0) / 100.0)
                    if self.equipment_cost_rate
                    else 0.0
                )
                month_cost += labor + materials + equipment
            cumulative += month_cost
            real_series.append(round(cumulative, 2))

        # Presupuesto planificado lineal hasta el presupuesto total
        total = float(self.budget_amount or 0.0)
        if total <= 0:
            planned = [0.0 for _ in months]
        else:
            step = total / (len(months) - 1 or 1)
            val = 0.0
            planned = []
            for _ in months:
                planned.append(round(val, 2))
                val += step
            planned[-1] = round(total, 2)

        return {"labels": labels, "real": real_series, "budget": planned}

