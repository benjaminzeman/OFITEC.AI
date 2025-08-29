from odoo import models, fields, api
from datetime import datetime, timedelta


class NextAction(models.Model):
    _name = "ofitec.next.action"
    _description = "Recomendaciones Inteligentes de Próximas Acciones"
    _order = "priority desc, create_date desc"

    name = fields.Char(string="Título de la Acción", required=True)
    description = fields.Text(string="Descripción Detallada", required=True)

    # Clasificación y prioridad
    action_type = fields.Selection(
        [
            ("immediate", "Acción Inmediata"),
            ("urgent", "Acción Urgente"),
            ("planned", "Acción Planificada"),
            ("preventive", "Acción Preventiva"),
        ],
        string="Tipo de Acción",
        required=True,
    )

    priority = fields.Selection(
        [
            ("1", "Crítica (1)"),
            ("2", "Alta (2)"),
            ("3", "Media (3)"),
            ("4", "Baja (4)"),
        ],
        string="Prioridad",
        required=True,
        default="3",
    )

    category = fields.Selection(
        [
            ("risk", "Gestión de Riesgos"),
            ("financial", "Gestión Financiera"),
            ("operational", "Operacional"),
            ("quality", "Calidad y Seguridad"),
            ("communication", "Comunicación"),
            ("planning", "Planificación"),
        ],
        string="Categoría",
        required=True,
    )

    # Contexto del proyecto
    project_id = fields.Many2one("project.project", string="Proyecto Relacionado")
    risk_id = fields.Many2one("ofitec.project.risk", string="Riesgo Relacionado")
    incident_id = fields.Many2one(
        "ofitec.site.incident", string="Incidente Relacionado"
    )
    budget_id = fields.Many2one(
        "ofitec.project.financials", string="Presupuesto Relacionado"
    )

    # Estado y seguimiento
    status = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("in_progress", "En Progreso"),
            ("completed", "Completada"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado",
        default="pending",
        required=True,
        tracking=True,
    )

    # Fechas importantes
    suggested_date = fields.Date(
        string="Fecha Sugerida", default=fields.Date.today, required=True
    )
    deadline = fields.Date(string="Fecha Límite")
    completed_date = fields.Date(string="Fecha de Completación")

    # Métricas de IA
    confidence_score = fields.Float(string="Puntuación de Confianza IA (%)", default=0)
    impact_score = fields.Float(string="Puntuación de Impacto", default=0)
    urgency_score = fields.Float(string="Puntuación de Urgencia", default=0)

    # Acciones recomendadas
    recommended_actions = fields.Text(string="Acciones Recomendadas")
    expected_benefits = fields.Text(string="Beneficios Esperados")
    required_resources = fields.Text(string="Recursos Requeridos")

    # Metadata
    created_by_ai = fields.Boolean(string="Creado por IA", default=True)
    ai_model_used = fields.Char(string="Modelo de IA Utilizado")
    user_id = fields.Many2one(
        "res.users", string="Asignado a", default=lambda self: self.env.user
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )

    @api.model
    def generate_next_actions(self, project_id=None):
        """Generar recomendaciones inteligentes de próximas acciones"""

        actions = []

        # Analizar riesgos críticos
        risk_actions = self._analyze_critical_risks(project_id)
        actions.extend(risk_actions)

        # Analizar situación financiera
        financial_actions = self._analyze_financial_situation(project_id)
        actions.extend(financial_actions)

        # Analizar incidentes activos
        incident_actions = self._analyze_active_incidents(project_id)
        actions.extend(incident_actions)

        # Analizar progreso del proyecto
        progress_actions = self._analyze_project_progress(project_id)
        actions.extend(progress_actions)

        # Analizar comunicación y reportes
        communication_actions = self._analyze_communication(project_id)
        actions.extend(communication_actions)

        # Crear acciones en la base de datos
        for action_data in actions:
            self.create(action_data)

        return len(actions)

    def cron_notify_urgent_actions(self):
        """Cron: enviar recordatorios por WhatsApp para acciones urgentes no enviadas.
        No requiere Enterprise. Depende de configuración de ofitec_whatsapp.
        """
        domain = [
            ("priority", "in", ["1", "2"]),
            ("whatsapp_enabled", "=", True),
            ("whatsapp_sent", "=", False),
        ]
        records = self.search(domain, limit=200)
        for rec in records:
            try:
                rec._send_whatsapp_notification()
            except Exception:
                # Evitar romper el cron por un fallo de red o configuración
                continue

    def _analyze_critical_risks(self, project_id=None):
        """Analizar riesgos críticos y generar acciones"""

        domain = [
            ("severity", "in", ["high", "critical"]),
            ("status", "not in", ["closed", "occurred"]),
        ]
        if project_id:
            domain.append(("project_id", "=", project_id))

        critical_risks = self.env["ofitec.project.risk"].search(domain)

        actions = []
        for risk in critical_risks:
            if risk.severity == "critical":
                priority = "1"
                action_type = "immediate"
            else:
                priority = "2"
                action_type = "urgent"

            actions.append(
                {
                    "name": f"Acción inmediata para riesgo crítico: {risk.name}",
                    "description": f"Se requiere atención inmediata para el riesgo: {risk.description}. "
                    f'Causa: {risk.causes or "Por determinar"}. '
                    f'Impacto potencial: {risk.consequences or "Significativo"}.',
                    "action_type": action_type,
                    "priority": priority,
                    "category": "risk",
                    "project_id": risk.project_id.id,
                    "risk_id": risk.id,
                    "confidence_score": 95.0,
                    "impact_score": 9.0 if risk.severity == "critical" else 7.0,
                    "urgency_score": 10.0 if risk.severity == "critical" else 8.0,
                    "recommended_actions": risk.mitigation_plan
                    or "Revisar y ejecutar plan de mitigación definido",
                    "expected_benefits": "Reducción significativa del riesgo y prevención de impactos mayores",
                    "required_resources": "Equipo responsable, recursos definidos en plan de mitigación",
                    "deadline": risk.deadline
                    or (datetime.now().date() + timedelta(days=7)),
                    "ai_model_used": "Risk Analysis Engine v2.0",
                }
            )

        return actions

    def _analyze_financial_situation(self, project_id=None):
        """Analizar situación financiera y generar acciones"""

        domain = [("state", "in", ["active", "approved"])]
        if project_id:
            domain.append(("project_id", "=", project_id))

        budgets = self.env["ofitec.project.financials"].search(domain)

        actions = []
        for budget in budgets:
            if budget.variance_percentage and budget.variance_percentage > 15:
                actions.append(
                    {
                        "name": f"Revisar varianza presupuestaria alta en {budget.project_id.name}",
                        "description": f"El proyecto presenta una varianza presupuestaria de {budget.variance_percentage:.1f}%. "
                        f"Costo estimado total: ${budget.estimated_total_cost:,.0f}. "
                        f"Presupuesto original: ${budget.budget_amount:,.0f}.",
                        "action_type": (
                            "urgent" if budget.variance_percentage > 25 else "planned"
                        ),
                        "priority": "1" if budget.variance_percentage > 25 else "2",
                        "category": "financial",
                        "project_id": budget.project_id.id,
                        "budget_id": budget.id,
                        "confidence_score": 90.0,
                        "impact_score": 8.0,
                        "urgency_score": (
                            9.0 if budget.variance_percentage > 25 else 6.0
                        ),
                        "recommended_actions": (
                            "Revisar causas de la varianza, ajustar presupuesto si es necesario, "
                            "implementar medidas de control de costos"
                        ),
                        "expected_benefits": "Mejor control financiero y prevención de desviaciones mayores",
                        "required_resources": "Equipo financiero, datos de costos actualizados",
                        "deadline": datetime.now().date() + timedelta(days=5),
                        "ai_model_used": "Financial Analysis Engine v1.5",
                    }
                )

        return actions

    def _analyze_active_incidents(self, project_id=None):
        """Analizar incidentes activos y generar acciones"""

        domain = [("state", "not in", ["resolved", "closed"])]
        if project_id:
            domain.append(("project_id", "=", project_id))

        active_incidents = self.env["ofitec.site.incident"].search(domain)

        actions = []
        for incident in active_incidents:
            priority = "2" if incident.severity in ["high", "critical"] else "3"
            action_type = (
                "urgent" if incident.severity in ["high", "critical"] else "planned"
            )

            actions.append(
                {
                    "name": f"Resolver incidente activo: {incident.name}",
                    "description": f"Incidente reportado: {incident.description}. "
                    f'Tipo: {dict(incident._fields["incident_type"].selection).get(incident.incident_type)}. '
                    f'Severidad: {dict(incident._fields["severity"].selection).get(incident.severity)}.',
                    "action_type": action_type,
                    "priority": priority,
                    "category": "operational",
                    "project_id": incident.project_id.id,
                    "incident_id": incident.id,
                    "confidence_score": 85.0,
                    "impact_score": 6.0 if incident.severity == "low" else 8.0,
                    "urgency_score": (
                        8.0 if incident.severity in ["high", "critical"] else 5.0
                    ),
                    "recommended_actions": incident.preventive_action
                    or "Investigar causa raíz y implementar solución",
                    "expected_benefits": "Resolución del incidente y prevención de recurrencia",
                    "required_resources": f'Responsable: {incident.responsible_id.name if incident.responsible_id else "Por asignar"}',
                    "deadline": incident.deadline
                    or (datetime.now().date() + timedelta(days=3)),
                    "ai_model_used": "Incident Analysis Engine v1.0",
                }
            )

        return actions

    def _analyze_project_progress(self, project_id=None):
        """Analizar progreso del proyecto y generar acciones"""

        domain = []
        if project_id:
            domain.append(("id", "=", project_id))

        projects = (
            self.env["project.project"].search(domain)
            if project_id
            else self.env["project.project"].search([])
        )

        actions = []
        for project in projects:
            # Calcular días desde último reporte
            last_report = self.env["ofitec.daily.report"].search(
                [("project_id", "=", project.id), ("state", "=", "approved")],
                order="date desc",
                limit=1,
            )

            days_since_last_report = 0
            if last_report:
                days_since_last_report = (datetime.now().date() - last_report.date).days

            # Generar acción si no hay reportes recientes
            if days_since_last_report > 3:
                actions.append(
                    {
                        "name": f"Actualizar reporte de progreso en {project.name}",
                        "description": f"No se han recibido reportes de progreso en los últimos {days_since_last_report} días. "
                        f'Último reporte: {last_report.date if last_report else "Nunca"}.',
                        "action_type": "planned",
                        "priority": "3",
                        "category": "operational",
                        "project_id": project.id,
                        "confidence_score": 75.0,
                        "impact_score": 4.0,
                        "urgency_score": 6.0,
                        "recommended_actions": "Solicitar actualización de progreso del proyecto",
                        "expected_benefits": "Mantener control y seguimiento actualizado del proyecto",
                        "required_resources": "Equipo de obra responsable del proyecto",
                        "deadline": datetime.now().date() + timedelta(days=2),
                        "ai_model_used": "Progress Monitoring Engine v1.2",
                    }
                )

        return actions

    def _analyze_communication(self, project_id=None):
        """Analizar comunicación y generar acciones"""

        actions = []

        # Verificar reportes pendientes de aprobación
        pending_reports = self.env["ofitec.daily.report"].search_count(
            [("state", "=", "submitted")]
        )

        if pending_reports > 0:
            actions.append(
                {
                    "name": f"Aprobar {pending_reports} reportes pendientes",
                    "description": f"Hay {pending_reports} reportes diarios pendientes de aprobación. "
                    "Es importante mantener el flujo de comunicación actualizado.",
                    "action_type": "planned",
                    "priority": "3",
                    "category": "communication",
                    "confidence_score": 80.0,
                    "impact_score": 5.0,
                    "urgency_score": 6.0,
                    "recommended_actions": "Revisar y aprobar reportes pendientes en el sistema",
                    "expected_benefits": "Mejora en la comunicación y seguimiento del proyecto",
                    "required_resources": "Supervisor o gerente de proyecto",
                    "deadline": datetime.now().date() + timedelta(days=1),
                    "ai_model_used": "Communication Analysis Engine v1.0",
                }
            )

        return actions

    def action_mark_completed(self):
        """Marcar acción como completada"""

        self.write({"status": "completed", "completed_date": datetime.now().date()})

    def action_start_progress(self):
        """Marcar acción como en progreso"""

        self.write({"status": "in_progress"})

    def action_cancel(self):
        """Cancelar acción"""

        self.write({"status": "cancelled"})

    @api.model
    def get_dashboard_data(self):
        """Obtener datos para el dashboard de próximas acciones"""

        # Acciones por estado
        pending_count = self.search_count([("status", "=", "pending")])
        in_progress_count = self.search_count([("status", "=", "in_progress")])
        completed_today = self.search_count(
            [
                ("status", "=", "completed"),
                ("completed_date", "=", datetime.now().date()),
            ]
        )

        # Acciones por prioridad
        critical_count = self.search_count(
            [("priority", "=", "1"), ("status", "=", "pending")]
        )
        high_count = self.search_count(
            [("priority", "=", "2"), ("status", "=", "pending")]
        )

        # Próximas acciones urgentes
        urgent_actions = self.search(
            [("status", "=", "pending"), ("priority", "in", ["1", "2"])],
            order="priority, suggested_date",
            limit=5,
        )

        return {
            "summary": {
                "pending": pending_count,
                "in_progress": in_progress_count,
                "completed_today": completed_today,
                "critical": critical_count,
                "high": high_count,
            },
            "urgent_actions": [
                {
                    "id": action.id,
                    "name": action.name,
                    "priority": action.priority,
                    "category": action.category,
                    "deadline": action.deadline,
                    "project": (
                        action.project_id.name if action.project_id else "General"
                    ),
                }
                for action in urgent_actions
            ],
        }

    @api.model
    def run_ai_analysis(self):
        """Ejecutar análisis completo con IA y generar recomendaciones"""

        # Limpiar acciones antiguas (más de 30 días)
        old_actions = self.search(
            [
                ("create_date", "<", datetime.now() - timedelta(days=30)),
                ("status", "in", ["completed", "cancelled"]),
            ]
        )
        old_actions.unlink()

        # Generar nuevas recomendaciones
        total_actions = self.generate_next_actions()

        return {
            "success": True,
            "actions_generated": total_actions,
            "message": f"Se generaron {total_actions} recomendaciones inteligentes",
        }
