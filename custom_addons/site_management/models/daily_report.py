from odoo import models, fields, api
from datetime import timedelta

class DailyReport(models.Model):
    _name = 'ofitec.daily.report'
    _description = 'Reporte Diario de Obra'
    _order = 'date desc'

    name = fields.Char(string='Título del Reporte', required=True, default=lambda self: f'Reporte {fields.Date.today()}')
    project_id = fields.Many2one('project.project', string='Proyecto', required=True, index=True)
    date = fields.Date(string='Fecha', default=fields.Date.today, required=True)
    progress = fields.Float(string='Progreso (%)', required=True, help='Porcentaje de avance del proyecto')

    # Información del trabajo realizado
    description = fields.Text(string='Trabajos Realizados', required=True)
    issues = fields.Text(string='Incidencias/Observaciones')
    weather = fields.Char(string='Condiciones Climáticas')
    team_size = fields.Integer(string='Personal en Obra', help='Número de trabajadores en sitio')
    hours_worked = fields.Float(string='Horas Trabajadas', help='Total de horas hombre trabajadas')

    # Recursos y materiales
    materials_used = fields.Text(string='Materiales Utilizados')
    equipment_used = fields.Text(string='Equipos Utilizados')
    subcontractors = fields.Text(string='Subcontratistas Presentes')

    # Calidad y seguridad
    safety_incidents = fields.Text(string='Incidentes de Seguridad')
    quality_checks = fields.Text(string='Controles de Calidad')
    photos = fields.Many2many('ir.attachment', string='Fotos/Evidencias')

    # Información adicional
    next_day_plan = fields.Text(string='Plan para Mañana')
    client_feedback = fields.Text(string='Comentarios del Cliente')
    supervisor_notes = fields.Text(string='Notas del Supervisor')

    # Metadata
    user_id = fields.Many2one('res.users', string='Reportado por', default=lambda self: self.env.user, required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('submitted', 'Enviado'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string='Estado', default='draft', required=True, tracking=True)

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = f'Reporte {vals.get("date", fields.Date.today())} - {self.env.user.name}'
        return super(DailyReport, self).create(vals)

    def action_submit(self):
        """Enviar reporte para aprobación"""
        self.write({'state': 'submitted'})

    def action_approve(self):
        """Aprobar reporte"""
        self.write({'state': 'approved'})
        # Integrar con project_financials para actualizar costos
        self._update_project_progress()
        self._update_financial_costs()
        # Verificar si hay incidentes críticos para convertir a riesgos
        self._check_critical_incidents()

    def action_reject(self):
        """Rechazar reporte"""
        self.write({'state': 'rejected'})

    def _update_project_progress(self):
        """Actualizar progreso del proyecto basado en reportes"""
        if self.project_id:
            # Calcular progreso promedio de los últimos reportes
            recent_reports = self.search([
                ('project_id', '=', self.project_id.id),
                ('state', '=', 'approved'),
                ('date', '>=', fields.Date.today() - timedelta(days=30))
            ], limit=10)

            if recent_reports:
                avg_progress = sum(r.progress for r in recent_reports) / len(recent_reports)
                self.project_id.write({'progress': avg_progress})

    def _update_financial_costs(self):
        """Actualizar costos financieros del proyecto"""
        if self.project_id:
            # Buscar presupuesto activo del proyecto
            budget = self.env['ofitec.project.financials'].search([
                ('project_id', '=', self.project_id.id),
                ('state', 'in', ['active', 'approved'])
            ], limit=1)

            if budget:
                # Forzar recálculo de costos
                budget._compute_progress_cost()
                budget._compute_estimated_total_cost()
                budget._compute_variance()

    def _check_critical_incidents(self):
        """Verificar si hay incidentes críticos que convertir a riesgos"""
        if self.safety_incidents or self.issues:
            # Crear incidentes automáticamente desde el reporte si hay problemas reportados
            incident_data = {
                'description': f'Incidente reportado en reporte diario: {self.issues or self.safety_incidents}',
                'type': 'safety' if self.safety_incidents else 'other',
                'severity': 'high' if 'crítico' in (self.issues or self.safety_incidents).lower() else 'medium'
            }
            incident = self.env['ofitec.site.incident'].create_from_report(self.id, incident_data)

            # Si es incidente crítico, convertir automáticamente a riesgo
            if incident.severity in ['high', 'critical']:
                risk = incident.action_convert_to_risk()
                if risk:
                    # Notificar al responsable del proyecto
                    self._notify_risk_creation(risk)

    def _notify_risk_creation(self, risk):
        """Notificar creación de riesgo al equipo del proyecto"""
        if self.project_id.user_id:
            self.env['mail.message'].create({
                'model': 'project.project',
                'res_id': self.project_id.id,
                'subject': f'Nuevo riesgo identificado: {risk.name}',
                'body': f'Se ha identificado un nuevo riesgo crítico en el proyecto {self.project_id.name}. '
                       f'Revise el registro de riesgos para más detalles.',
                'message_type': 'notification',
                'partner_ids': [(4, self.project_id.user_id.partner_id.id)]
            })
        """Actualizar progreso del proyecto basado en reportes"""
        if self.project_id:
            # Calcular progreso promedio de los últimos reportes
            recent_reports = self.search([
                ('project_id', '=', self.project_id.id),
                ('state', '=', 'approved'),
                ('date', '>=', fields.Date.today() - timedelta(days=30))
            ], limit=10)

            if recent_reports:
                avg_progress = sum(r.progress for r in recent_reports) / len(recent_reports)
                self.project_id.write({'progress': avg_progress})

    @api.model
    def create_from_whatsapp(self, message_data):
        """Crear reporte desde mensaje de WhatsApp"""
        return self.create({
            'name': f'Reporte WhatsApp {message_data.get("date", fields.Date.today())}',
            'description': message_data.get('message', ''),
            'project_id': message_data.get('project_id'),
            'date': message_data.get('date', fields.Date.today()),
            'state': 'submitted'  # Los reportes de WhatsApp van directo a enviados
        })
