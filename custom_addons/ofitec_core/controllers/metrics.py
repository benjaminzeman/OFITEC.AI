from time import time
from odoo import http
from odoo.http import request

try:
    from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST  # type: ignore

    PROM_AVAILABLE = True
except Exception:
    PROM_AVAILABLE = False


_simple_started = time()
_simple_requests = 0


class MetricsController(http.Controller):
    @http.route("/ofitec/metrics", type="http", auth="public")
    def metrics(self):
        if PROM_AVAILABLE:
            registry = CollectorRegistry()
            req_counter = Counter(
                "ofitec_requests_total",
                "Total de requests JSON OFITEC",
                ["endpoint"],
                registry=registry,
            )
            db_hist = Histogram(
                "ofitec_db_latency_seconds",
                "Tiempo de consulta a DB",
                registry=registry,
            )

            # Simple sample metrics using current request
            req_counter.labels(endpoint="metrics").inc()
            # Observe a tiny value just to produce series
            db_hist.observe(0.001)

            output = generate_latest(registry)
            return request.make_response(
                output, headers=[("Content-Type", CONTENT_TYPE_LATEST)]
            )

        # Fallback plano en formato tipo Prometheus básico
        global _simple_requests
        _simple_requests += 1
        body = []
        body.append("# HELP ofitec_up 1 si el servicio está vivo")
        body.append("# TYPE ofitec_up gauge")
        body.append("ofitec_up 1")
        body.append("# HELP ofitec_uptime_seconds Uptime del proceso")
        body.append("# TYPE ofitec_uptime_seconds counter")
        body.append(f"ofitec_uptime_seconds {int(time() - _simple_started)}")
        body.append("# HELP ofitec_requests_total Total de requests a métricas")
        body.append("# TYPE ofitec_requests_total counter")
        body.append(f'ofitec_requests_total {{endpoint="metrics"}} {_simple_requests}')
        return request.make_response(
            "\n".join(body), headers=[("Content-Type", "text/plain; version=0.0.4")]
        )
