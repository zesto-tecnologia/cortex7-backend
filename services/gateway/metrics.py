"""
Prometheus metrics for Gateway service authentication monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge

# Authentication metrics
auth_validations_total = Counter(
    "gateway_auth_validations_total",
    "Total number of authentication validation attempts",
    ["result", "service"]
)

auth_validation_duration_seconds = Histogram(
    "gateway_auth_validation_duration_seconds",
    "Time spent validating authentication tokens",
    ["result"]
)

canary_requests_total = Counter(
    "gateway_canary_requests_total",
    "Total requests processed by canary deployment",
    ["authenticated"]
)

active_authenticated_requests = Gauge(
    "gateway_active_authenticated_requests",
    "Number of currently active authenticated requests"
)

# Proxy metrics
proxy_requests_total = Counter(
    "gateway_proxy_requests_total",
    "Total proxy requests",
    ["service", "method", "status_code"]
)

proxy_duration_seconds = Histogram(
    "gateway_proxy_duration_seconds",
    "Time spent proxying requests to backend services",
    ["service", "method"]
)


class AuthMetrics:
    """Convenience class for accessing auth metrics."""

    def __init__(self):
        self.auth_validations_total = auth_validations_total
        self.auth_validation_duration_seconds = auth_validation_duration_seconds
        self.canary_requests_total = canary_requests_total
        self.active_authenticated_requests = active_authenticated_requests
        self.proxy_requests_total = proxy_requests_total
        self.proxy_duration_seconds = proxy_duration_seconds


# Singleton instance
auth_metrics = AuthMetrics()
