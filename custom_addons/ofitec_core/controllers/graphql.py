from odoo import http
from odoo.http import request

try:
    import graphene  # type: ignore

    GRAPHENE_AVAILABLE = True
except Exception:
    GRAPHENE_AVAILABLE = False


def _build_schema():
    """Build a minimal GraphQL schema if graphene is available.
    Exposes read‑only queries for core objects. Does not require Enterprise.
    """
    if not GRAPHENE_AVAILABLE:
        return None

    class Project(graphene.ObjectType):
        id = graphene.Int()
        name = graphene.String()
        state = graphene.String()
        progress = graphene.Float()

    class Risk(graphene.ObjectType):
        id = graphene.Int()
        name = graphene.String()
        risk_category = graphene.String()
        severity = graphene.String()
        risk_exposure = graphene.Float()

    class Financial(graphene.ObjectType):
        id = graphene.Int()
        project_id = graphene.Int()
        budget_amount = graphene.Float()
        progress_cost = graphene.Float()
        estimated_total_cost = graphene.Float()
        variance_amount = graphene.Float()
        variance_percentage = graphene.Float()

    class DailyReport(graphene.ObjectType):
        id = graphene.Int()
        name = graphene.String()
        project_id = graphene.Int()
        date = graphene.String()
        progress = graphene.Float()

    class Query(graphene.ObjectType):
        projects = graphene.List(Project, name=graphene.String())
        risks = graphene.List(Risk, project_id=graphene.Int())
        financials = graphene.List(Financial, project_id=graphene.Int())
        reports = graphene.List(
            DailyReport, project_id=graphene.Int(), limit=graphene.Int()
        )

        def resolve_projects(self, info, name=None):
            env = request.env
            domain = []
            if name:
                domain.append(("name", "ilike", name))
            recs = env["project.project"].sudo().search(domain, limit=100)
            return [
                Project(
                    id=r.id,
                    name=r.name,
                    state=getattr(r, "state", ""),
                    progress=getattr(r, "progress", 0.0),
                )
                for r in recs
            ]

        def resolve_risks(self, info, project_id=None):
            env = request.env
            domain = []
            if project_id:
                domain.append(("project_id", "=", project_id))
            recs = env["ofitec.project.risk"].sudo().search(domain, limit=200)
            return [
                Risk(
                    id=r.id,
                    name=r.name,
                    risk_category=getattr(r, "risk_category", ""),
                    severity=getattr(r, "severity", ""),
                    risk_exposure=getattr(r, "risk_exposure", 0.0),
                )
                for r in recs
            ]

        def resolve_financials(self, info, project_id=None):
            env = request.env
            domain = []
            if project_id:
                domain.append(("project_id", "=", project_id))
            recs = env["ofitec.project.financials"].sudo().search(domain, limit=100)
            return [
                Financial(
                    id=b.id,
                    project_id=getattr(b.project_id, "id", False) or 0,
                    budget_amount=getattr(b, "budget_amount", 0.0),
                    progress_cost=getattr(b, "progress_cost", 0.0),
                    estimated_total_cost=getattr(b, "estimated_total_cost", 0.0),
                    variance_amount=getattr(b, "variance_amount", 0.0),
                    variance_percentage=getattr(b, "variance_percentage", 0.0),
                )
                for b in recs
            ]

        def resolve_reports(self, info, project_id=None, limit=50):
            env = request.env
            domain = []
            if project_id:
                domain.append(("project_id", "=", project_id))
            recs = (
                env["ofitec.daily.report"]
                .sudo()
                .search(domain, order="date desc", limit=limit)
            )
            return [
                DailyReport(
                    id=r.id,
                    name=r.name,
                    project_id=getattr(r.project_id, "id", False) or 0,
                    date=str(getattr(r, "date", "")),
                    progress=getattr(r, "progress", 0.0),
                )
                for r in recs
            ]

    return graphene.Schema(query=Query)


class GraphQLController(http.Controller):
    @http.route(
        "/ofitec/graphql", type="json", auth="user", methods=["POST"], csrf=False
    )
    def graphql_endpoint(self, **kwargs):
        if not GRAPHENE_AVAILABLE:
            return {
                "success": False,
                "error": "GraphQL no disponible: falta dependencias (graphene).",
                "hint": 'Instalar paquete python "graphene" dentro del contenedor Odoo.',
            }

        query = kwargs.get("query") or kwargs.get("q")
        variables = kwargs.get("variables")
        if not query:
            return {"success": False, "error": 'Falta parámetro "query"'}

        schema = _build_schema()
        result = schema.execute(query, variable_values=variables)
        data = {}
        if result.data:
            data = result.data
        if result.errors:
            return {
                "success": False,
                "errors": [str(e) for e in result.errors],
                "data": data,
            }
        return {"success": True, "data": data}
