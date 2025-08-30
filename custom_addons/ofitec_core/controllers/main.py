from odoo import http
from odoo.http import request
import json


class OfitecCoreController(http.Controller):

    @http.route("/ofitec/api/health", type="json", auth="public", methods=["GET"])
    def health_check(self):
        """Endpoint de verificación de salud (JSON-RPC)"""
        return {"status": "ok", "message": "OFITEC Core API is running"}

    @http.route("/ofitec/health", type="http", auth="public", methods=["GET"])  # simple HTTP
    def health_http(self):
        """Health check simple por HTTP plano (para smoke tests y load balancers)."""
        payload = {"status": "ok", "service": "ofitec_core", "version": "16"}
        return request.make_response(
            json.dumps(payload), headers=[("Content-Type", "application/json")]
        )

    @http.route("/ofitec/api/projects", type="json", auth="user", methods=["GET"])
    def get_projects(self):
        """Obtener lista de proyectos del usuario actual"""
        projects = request.env["project.project"].search(
            [("user_id", "=", request.env.user.id)]
        )
        return {
            "projects": [
                {"id": p.id, "name": p.name, "state": p.state} for p in projects
            ]
        }

    @http.route("/ofitec/api/dashboard", type="json", auth="user", methods=["GET"])
    def get_dashboard_data(self):
        """Datos para el dashboard principal"""
        user = request.env.user
        projects = request.env["project.project"].search([("user_id", "=", user.id)])

        return {
            "user": {
                "name": user.name,
                "projects_count": len(projects),
                "active_projects": len(
                    projects.filtered(lambda p: p.state == "active")
                ),
            },
            "recent_projects": [
                {"id": p.id, "name": p.name, "progress": getattr(p, "progress", 0)}
                for p in projects[:5]
            ],
        }
