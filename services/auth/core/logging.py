"""Structured logging configuration for the application."""

import structlog
import logging
from services.auth.config import settings


def configure_logging():
    """Configure structlog for clean, structured logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.ENVIRONMENT != "development"
                else structlog.dev.ConsoleRenderer(colors=True)
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set log level
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.LOG_LEVEL),
    )

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("h2").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str = __name__):
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Logging Guidelines:
#
# ERROR: System failures, exceptions that prevent normal operation
#   - Database connection failures
#   - Supabase API errors
#   - Redis connection issues
#   - Authentication/authorization failures
#   Example: logger.error(f"Database connection failed: {error}")
#
# WARNING: Degraded functionality, security concerns, or unexpected behavior
#   - Failed login attempts (security)
#   - Rate limit exceeded
#   - Cache miss (performance degradation)
#   - Deprecated API usage
#   Example: logger.warning(f"Failed login attempt: {email}")
#
# INFO: Key business events and state changes
#   - User registration
#   - Successful login/logout
#   - Password reset initiated
#   - Service startup/shutdown
#   Example: logger.info(f"User registered: {email}")
#
# DEBUG: Detailed information for debugging (not in production)
#   - Request/response payloads
#   - Database queries
#   - Cache operations
#   - External API calls
#   Example: logger.debug(f"Supabase response: {response}")
#
# DO NOT LOG:
#   - Every function entry/exit
#   - Successful database queries (unless debugging)
#   - Redundant state information
#   - Sensitive data (passwords, tokens, PII)
