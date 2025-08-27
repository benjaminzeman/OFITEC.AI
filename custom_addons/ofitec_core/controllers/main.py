from odoo import http
from odoo.http import request

class OfitecCoreController(http.Controller):

    @http.route('/ofitec/api/health', type='json', auth='public', methods=['GET'])
    def health_check(self):
        """Endpoint de verificación de salud del sistema"""
        return {'status': 'ok', 'message': 'OFITEC Core API is running'}

    @http.route('/ofitec/api/projects', type='json', auth='user', methods=['GET'])
    def get_projects(self):
        """Obtener lista de proyectos del usuario actual"""
        projects = request.env['project.project'].search([
            ('user_id', '=', request.env.user.id)
        ])
        return {
            'projects': [{
                'id': p.id,
                'name': p.name,
                'state': p.state
            } for p in projects]
        }

    @http.route('/ofitec/api/dashboard', type='json', auth='user', methods=['GET'])
    def get_dashboard_data(self):
        """Datos para el dashboard principal"""
        user = request.env.user
        projects = request.env['project.project'].search([
            ('user_id', '=', user.id)
        ])

        return {
            'user': {
                'name': user.name,
                'projects_count': len(projects),
                'active_projects': len(projects.filtered(lambda p: p.state == 'active'))
            },
            'recent_projects': [{
                'id': p.id,
                'name': p.name,
                'progress': getattr(p, 'progress', 0)
            } for p in projects[:5]]
        }
