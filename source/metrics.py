"""Per-process HTTP measurements with a registry owned by each server."""

from time import perf_counter

from prometheus_client import CollectorRegistry, Counter, Histogram
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class HTTPMetrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "waygate_requests_total", "Completed HTTP requests", registry=self.registry
        )
        self.errors = Counter(
            "waygate_errors_total",
            "HTTP responses with status >= 400",
            registry=self.registry,
        )
        self.duration = Histogram(
            "waygate_response_time_seconds",
            "HTTP request duration",
            buckets=(0.1, 0.5, 1.0),
            registry=self.registry,
        )


class MetricsMiddleware:
    def __init__(self, app: ASGIApp, metrics: HTTPMetrics) -> None:
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") == "/metrics":
            await self.app(scope, receive, send)
            return
        start = perf_counter()
        status = 500

        async def measured_send(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, measured_send)
        except BaseException:
            status = 500
            raise
        finally:
            self.metrics.requests.inc()
            if status >= 400:
                self.metrics.errors.inc()
            self.metrics.duration.observe(perf_counter() - start)
