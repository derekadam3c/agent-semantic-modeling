"""Logging configuration with Application Insights integration.

Provides structured logging with OpenTelemetry and Application Insights export.
Supports local development with Rich console output and production telemetry.
"""

import logging
import sys
from typing import Optional

from rich.logging import RichHandler
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from .config import settings


# Global logger instances
_logger_initialized = False
_tracer_provider: Optional[TracerProvider] = None


def setup_logging(level: Optional[str] = None) -> None:
    """Configure logging with Application Insights integration.
    
    Sets up:
    - Rich console logging for development
    - OpenTelemetry tracing for Application Insights
    - Structured log format with correlation IDs
    - Exception tracking and telemetry
    
    Args:
        level: Optional logging level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _logger_initialized, _tracer_provider
    
    if _logger_initialized:
        return
    
    log_level = level or settings.log_level
    
    # Configure root logger with Rich handler
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)]
    )
    
    # Configure Azure SDK logging (reduce noise)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
        logging.WARNING
    )
    logging.getLogger("azure.identity").setLevel(logging.WARNING)
    
    # Setup OpenTelemetry tracing if Application Insights is configured
    if settings.app_insights_connection_string:
        _setup_application_insights()
    
    _logger_initialized = True


def _setup_application_insights() -> None:
    """Configure Application Insights with OpenTelemetry.
    
    Sets up:
    - TracerProvider with resource attributes
    - Azure Monitor exporter for traces and logs
    - Logging instrumentation for automatic log correlation
    """
    global _tracer_provider
    
    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter, AzureMonitorLogExporter
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        
        # Create resource with service attributes
        resource = Resource.create({
            "service.name": "pbi-semantic-modeling-agent",
            "service.version": settings.version,
            "deployment.environment": settings.environment,
        })
        
        # Setup trace provider
        _tracer_provider = TracerProvider(resource=resource)
        trace_exporter = AzureMonitorTraceExporter(
            connection_string=settings.app_insights_connection_string
        )
        _tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(_tracer_provider)
        
        # Setup log provider
        logger_provider = LoggerProvider(resource=resource)
        log_exporter = AzureMonitorLogExporter(
            connection_string=settings.app_insights_connection_string
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        
        # Add OpenTelemetry logging handler
        handler = LoggingHandler(logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)
        
        # Instrument logging for automatic correlation
        LoggingInstrumentor().instrument(set_logging_format=False)
        
        logging.info(
            "Application Insights configured",
            extra={"environment": settings.environment, "version": settings.version}
        )
        
    except ImportError as e:
        logging.warning(
            f"Application Insights dependencies not available: {e}. "
            "Install azure-monitor-opentelemetry-exporter for full telemetry support."
        )
    except Exception as e:
        logging.error(f"Failed to configure Application Insights: {e}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with structured logging support.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Configured logger instance with Application Insights correlation
    """
    return logging.getLogger(name)


def get_tracer(name: str) -> trace.Tracer:
    """Get an OpenTelemetry tracer for distributed tracing.
    
    Args:
        name: Tracer name (typically __name__ of the module)
        
    Returns:
        Tracer instance for creating spans
    """
    if _tracer_provider is None:
        # Fallback to global tracer provider
        return trace.get_tracer(name)
    return _tracer_provider.get_tracer(name)


def log_exception(logger: logging.Logger, exc: Exception, **extra_context) -> None:
    """Log an exception with full context and telemetry.
    
    Args:
        logger: Logger instance
        exc: Exception to log
        **extra_context: Additional context key-value pairs
    """
    logger.exception(
        f"Exception occurred: {exc.__class__.__name__}",
        exc_info=exc,
        extra=extra_context,
        stack_info=True
    )
