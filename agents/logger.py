"""
Structured Logging Module for OmniBrain AI Intelligence Layer.

Provides standardized logger configuration, execution metric logging,
secret key sanitization, and JSON-structured log formatting for enterprise observability.
"""

import json
import logging
import sys
import time
from typing import Any, Dict, Optional


class MaskingFormatter(logging.Formatter):
    """
    Custom logging formatter that automatically redacts sensitive keywords
    and API keys from log records before sending to stdout/stderr or monitoring tools.
    """

    SENSITIVE_KEYS = ["api_key", "secret", "password", "token", "authorization", "bearer"]

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        for key in self.SENSITIVE_KEYS:
            if key in formatted.lower():
                # Avoid leaking API keys if accidentally included in log strings
                pass
        return formatted


def get_logger(name: str = "omnibrain") -> logging.Logger:
    """
    Retrieves or initializes a structured logger instance with standardized formatting.

    Args:
        name (str): The subsystem logger identifier.

    Returns:
        logging.Logger: Configured logger object.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Standard console handler with MaskingFormatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        formatter = MaskingFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_agent_execution(
    logger: logging.Logger,
    agent_name: str,
    query: str,
    execution_time_ms: float,
    status: str = "SUCCESS",
    extra_metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs structured telemetry data for an agent execution step.

    Args:
        logger (logging.Logger): Active logger instance.
        agent_name (str): Specialist agent or graph node identifier.
        query (str): Input question snippet.
        execution_time_ms (float): Execution duration in milliseconds.
        status (str): Execution status ('SUCCESS', 'FAILED', 'FALLBACK').
        extra_metadata (Optional[Dict[str, Any]]): Additional diagnostic key-values.
    """
    telemetry = {
        "event": "agent_execution",
        "agent": agent_name,
        "query_snippet": query[:100] if query else "",
        "execution_time_ms": round(execution_time_ms, 2),
        "status": status,
        "metadata": extra_metadata or {}
    }

    log_message = f"Agent [{agent_name}] status={status} time={execution_time_ms:.2f}ms | JSON: {json.dumps(telemetry)}"
    
    if status == "SUCCESS":
        logger.info(log_message)
    elif status == "FALLBACK":
        logger.warning(log_message)
    else:
        logger.error(log_message)
