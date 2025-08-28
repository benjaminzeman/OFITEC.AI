from odoo import models, fields, api
from datetime import timedelta


class ProjectBudget(models.Model):
    _name = "ofitec.project.financials"
    _description = "Presupuesto y Costos de Proyecto"
    _order = "create_date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nombre del Presupuesto", required=True)
    project_id = fields.Many2one(
        "project.project", string="Proyecto", required=True, index=True
    )

    # Información básica del presupuesto
    budget_amount = fields.Monetary(
        string="Monto Total del Presupuesto",
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
    )
    start_date = fields.Date(string="Fecha de Inicio", required=True)
    end_date = fields.Date(string="Fecha de Fin", required=True)

    # Tasas y costos
    cost_rate = fields.Monetary(
        string="Tasa de Costo por Hora", currency_field="currency_id"
    )
    material_cost_rate = fields.Monetary(
        string="Tasa de Costos de Materiales", currency_field="currency_id"
    )
    equipment_cost_rate = fields.Monetary(
        string="Tasa de Costos de Equipos", currency_field="currency_id"
    )

    # Costos calculados automáticamente
    progress_cost = fields.Monetary(
        string="Costo Real del Progreso",
        compute="_compute_progress_cost",
        store=True,
        currency_field="currency_id",
    )
    estimated_total_cost = fields.Monetary(
        string="Costo Total Estimado",
        compute="_compute_estimated_total_cost",
        store=True,
        currency_field="currency_id",
    )
    variance_amount = fields.Monetary(
        string="Varianza (Presupuesto vs Real)",
        compute="_compute_variance",
        store=True,
        currency_field="currency_id",
    )
    variance_percentage = fields.Float(
        string="Varianza (%)", compute="_compute_variance", store=True
    )

    # Estado y control
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("approved", "Aprobado"),
            ("active", "Activo"),
            ("completed", "Completado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
    )

    # Metadata
    user_id = fields.Many2one(
        "res.users",
        string="Creado por",
        default=lambda self: self.env.user,
        required=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )
    approval_date = fields.Date(string="Fecha de Aprobación")

    @api.depends("project_id", "cost_rate", "material_cost_rate", "equipment_cost_rate")
    def _compute_progress_cost(self):
        for record in self:
            if record.project_id:
                # Obtener reportes de los últimos 30 días
                date_limit = fields.Date.today() - timedelta(days=30)
                reports = self.env["ofitec.daily.report"].search(
                    [
                        ("project_id", "=", record.project_id.id),
                        ("state", "=", "approved"),
                        ("date", ">=", date_limit),
                    ]
                )

                total_cost = 0
                for report in reports:
                    # Calcular costo basado en horas trabajadas y tasas
                    labor_cost = (report.hours_worked or 0) * record.cost_rate
                    # Estimar costos de materiales y equipos (porcentaje del costo de mano de obra)
                    material_cost = (
                        labor_cost * (record.material_cost_rate / 100)
                        if record.material_cost_rate
                        else 0
                    )
                    equipment_cost = (
                        labor_cost * (record.equipment_cost_rate / 100)
                        if record.equipment_cost_rate
                        else 0
                    )
                    total_cost += labor_cost + material_cost + equipment_cost

                record.progress_cost = total_cost

    @api.depends("budget_amount", "progress_cost", "project_id.progress")
    def _compute_estimated_total_cost(self):
        for record in self:
            if (
                record.project_id
                and record.project_id.progress
                and record.project_id.progress > 0
            ):
                # Estimar costo total basado en progreso actual
                progress_percentage = record.project_id.progress / 100
                if progress_percentage > 0:
                    record.estimated_total_cost = (
                        record.progress_cost / progress_percentage
                    )
                else:
                    record.estimated_total_cost = 0
            else:
                record.estimated_total_cost = 0

    @api.depends("budget_amount", "estimated_total_cost")
    def _compute_variance(self):
        for record in self:
            if record.estimated_total_cost and record.budget_amount:
                record.variance_amount = (
                    record.estimated_total_cost - record.budget_amount
                )
                record.variance_percentage = (
                    record.variance_amount / record.budget_amount
                ) * 100
            else:
                record.variance_amount = 0
                record.variance_percentage = 0

    def action_approve(self):
        """Aprobar presupuesto"""
        self.write({"state": "approved", "approval_date": fields.Date.today()})

    def action_activate(self):
        """Activar presupuesto"""
        self.write({"state": "active"})

    def action_complete(self):
        """Marcar como completado"""
        self.write({"state": "completed"})

    def action_cancel(self):
        """Cancelar presupuesto"""
        self.write({"state": "cancelled"})

    def update_costs_from_progress(self, project_id=None):
        """Actualizar costos basado en reportes de progreso"""
        if project_id:
            records = self.search(
                [
                    ("project_id", "=", project_id),
                    ("state", "in", ["active", "approved"]),
                ]
            )
        else:
            records = self.search([("state", "in", ["active", "approved"])])

        for record in records:
            record._compute_progress_cost()
            record._compute_estimated_total_cost()
            record._compute_variance()

    @api.model
    def create_invoice_from_budget(self, budget):
        """Crear factura desde presupuesto (placeholder para integración con account)"""
        # Esta función se implementará cuando integremos con el módulo account
        pass
