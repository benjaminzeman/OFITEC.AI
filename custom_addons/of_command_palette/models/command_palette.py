from odoo import models, fields, api
from datetime import datetime


class CommandPalette(models.Model):
    _name = "ofitec.command.palette"
    _description = "Command Palette Inteligente OFITEC.AI"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Comando", required=True)
    command_type = fields.Selection(
        [
            ("action", "Acción del Sistema"),
            ("query", "Consulta de Datos"),
            ("analysis", "Análisis Inteligente"),
            ("prediction", "Predicción"),
            ("automation", "Automatización"),
        ],
        string="Tipo de Comando",
        required=True,
    )

    description = fields.Text(string="Descripción")
    keywords = fields.Char(string="Palabras Clave", help="Separadas por comas")
    is_active = fields.Boolean(string="Activo", default=True)
    usage_count = fields.Integer(string="Veces Usado", default=0)
    last_used = fields.Datetime(string="Último Uso")

    # Configuración avanzada
    ai_enabled = fields.Boolean(string="IA Habilitada", default=True)
    requires_context = fields.Boolean(string="Requiere Contexto", default=False)
    context_fields = fields.Char(
        string="Campos de Contexto", help="Campos necesarios para ejecutar el comando"
    )
    user_id = fields.Many2one(
        "res.users",
        string="Creado por",
        default=lambda self: self.env.user,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        readonly=True,
    )

    @api.model
    def execute_command(self, command_text, context=None):
        """Ejecutar comando inteligente con IA"""

        # Incrementar contador de uso
        command = self._find_command(command_text)
        if command:
            command.usage_count += 1
            command.last_used = datetime.now()

        # Procesar comando con IA
        result = self._process_with_ai(command_text, context)

        return result

    def _find_command(self, command_text):
        """Encontrar comando más relevante usando IA"""

        # Buscar por palabras clave exactas primero
        for command in self.search([("is_active", "=", True)]):
            if command.keywords:
                keywords = [k.strip().lower() for k in command.keywords.split(",")]
                command_words = command_text.lower().split()

                # Si hay coincidencia exacta de palabras clave
                if any(keyword in command_words for keyword in keywords):
                    return command

        # Si no hay coincidencia exacta, usar análisis de similitud
        return self._find_best_match(command_text)

    def _find_best_match(self, command_text):
        """Encontrar mejor coincidencia usando análisis de similitud"""

        best_match = None
        best_score = 0

        for command in self.search([("is_active", "=", True)]):
            score = self._calculate_similarity(
                command_text, command.name + " " + (command.keywords or "")
            )

            if score > best_score:
                best_score = score
                best_match = command

        return best_match

    def _calculate_similarity(self, text1, text2):
        """Calcular similitud entre textos usando análisis simple"""

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0

        return len(intersection) / len(union)

    def _process_with_ai(self, command_text, context=None):
        """Procesar comando usando IA integrada"""

        # Intentar usar ai_bridge si está disponible
        try:
            ai_service = self.env["ai.bridge"]
            if ai_service:
                return self._ai_powered_processing(command_text, context)
        except Exception:
            pass

        # Procesamiento básico si IA no está disponible
        return self._basic_processing(command_text, context)

    def _ai_powered_processing(self, command_text, context=None):
        """Procesamiento inteligente con IA"""

        ai_bridge = self.env["ai.bridge"].search([], limit=1)

        if not ai_bridge:
            return self._basic_processing(command_text, context)

        # Análisis de intención del comando
        intent = self._analyze_intent(command_text)

        if intent == "project_status":
            return self._get_project_status(context)
        elif intent == "risk_analysis":
            return self._get_risk_analysis(context)
        elif intent == "cost_analysis":
            return self._get_cost_analysis(context)
        elif intent == "create_report":
            return self._create_daily_report(context)
        elif intent == "predict_costs":
            return ai_bridge.predict_costs(
                context.get("project_id") if context else None
            )
        else:
            return self._basic_processing(command_text, context)

    def _analyze_intent(self, command_text):
        """Analizar intención del comando usando IA"""

        text = command_text.lower()

        # Patrones de intención
        if any(word in text for word in ["estado", "status", "progreso", "avance"]):
            return "project_status"
        elif any(word in text for word in ["riesgo", "risk", "peligro"]):
            return "risk_analysis"
        elif any(
            word in text for word in ["costo", "cost", "presupuesto", "budget", "gasto"]
        ):
            return "cost_analysis"
        elif any(word in text for word in ["reporte", "report", "diario"]):
            return "create_report"
        elif any(word in text for word in ["predecir", "predict", "futuro", "estimar"]):
            return "predict_costs"

        return "general"

    def _get_project_status(self, context=None):
        """Obtener estado del proyecto"""

        project_id = context.get("project_id") if context else None

        if project_id:
            project = self.env["project.project"].browse(project_id)
            reports = self.env["ofitec.daily.report"].search(
                [("project_id", "=", project_id), ("state", "=", "approved")], limit=5
            )

            return {
                "type": "project_status",
                "project": project.name,
                "progress": project.progress,
                "recent_reports": len(reports),
                "last_report": reports[0].date if reports else None,
            }

        # Resumen general
        projects = self.env["project.project"].search([])
        total_projects = len(projects)
        active_projects = len(
            projects.filtered(lambda p: p.state not in ["done", "cancelled"])
        )

        return {
            "type": "project_status",
            "total_projects": total_projects,
            "active_projects": active_projects,
            "avg_progress": (
                sum(p.progress for p in projects) / total_projects
                if total_projects
                else 0
            ),
        }

    def _get_risk_analysis(self, context=None):
        """Obtener análisis de riesgos"""

        project_id = context.get("project_id") if context else None
        domain = [("status", "not in", ["closed", "occurred"])]
        if project_id:
            domain.append(("project_id", "=", project_id))

        risks = self.env["ofitec.project.risk"].search(domain)

        return {
            "type": "risk_analysis",
            "total_risks": len(risks),
            "critical_risks": len(risks.filtered(lambda r: r.severity == "critical")),
            "high_risks": len(risks.filtered(lambda r: r.severity == "high")),
            "categories": self._group_risks_by_category(risks),
        }

    def _get_cost_analysis(self, context=None):
        """Obtener análisis de costos"""

        project_id = context.get("project_id") if context else None
        domain = [("state", "in", ["active", "approved"])]
        if project_id:
            domain.append(("project_id", "=", project_id))

        budgets = self.env["ofitec.project.financials"].search(domain)

        if budgets:
            total_budget = sum(b.budget_amount for b in budgets)
            total_cost = sum(b.progress_cost for b in budgets)
            avg_variance = sum(b.variance_percentage for b in budgets) / len(budgets)

            return {
                "type": "cost_analysis",
                "total_budget": total_budget,
                "total_cost": total_cost,
                "avg_variance": avg_variance,
                "projects_count": len(budgets),
            }

        return {"type": "cost_analysis", "message": "No hay presupuestos activos"}

    def _create_daily_report(self, context=None):
        """Crear reporte diario inteligente"""

        if not context or not context.get("project_id"):
            return {
                "type": "error",
                "message": "Se requiere especificar el proyecto para crear un reporte",
            }

        # Crear reporte con datos básicos
        report_data = {
            "project_id": context.get("project_id"),
            "date": datetime.now().date(),
            "progress": context.get("progress", 0),
            "description": context.get(
                "description", "Reporte generado por Command Palette"
            ),
            "state": "draft",
        }

        report = self.env["ofitec.daily.report"].create(report_data)

        return {
            "type": "daily_report_created",
            "report_id": report.id,
            "message": f"Reporte diario creado para el proyecto {report.project_id.name}",
        }

    def _group_risks_by_category(self, risks):
        """Agrupar riesgos por categoría"""

        categories = {}
        for risk in risks:
            cat = risk.risk_category
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        return categories

    def _basic_processing(self, command_text, context=None):
        """Procesamiento básico sin IA"""

        text = command_text.lower()

        # Comandos básicos
        if "ayuda" in text or "help" in text:
            return {
                "type": "help",
                "message": "Comandos disponibles: estado, riesgos, costos, reporte, predecir",
            }
        elif "estado" in text or "status" in text:
            return self._get_project_status(context)
        elif "riesgo" in text or "risk" in text:
            return self._get_risk_analysis(context)
        elif "costo" in text or "cost" in text:
            return self._get_cost_analysis(context)
        else:
            return {
                "type": "unknown",
                "message": f"Comando no reconocido: {command_text}",
            }

    @api.model
    def get_command_suggestions(self, partial_command):
        """Obtener sugerencias de comandos"""

        commands = self.search([("is_active", "=", True)])
        suggestions = []

        for command in commands:
            if partial_command.lower() in command.name.lower():
                suggestions.append(
                    {
                        "id": command.id,
                        "name": command.name,
                        "description": command.description,
                        "type": command.command_type,
                    }
                )

        return suggestions[:10]  # Limitar a 10 sugerencias

    @api.model
    def learn_from_usage(self, command_text, result_type, success=True):
        """Aprender del uso de comandos para mejorar sugerencias"""

        # Esta función puede ser usada para machine learning
        # Por ahora solo registra el uso
        pass
