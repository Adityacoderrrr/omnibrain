"""
Structured Logging Module for OmniBrain AI Intelligence Layer.

Provides standardized logger configuration, execution metric logging,
secret key sanitization, and JSON-structured log formatting for enterprise observability.
"""

import json
import logging
import re
import sys
import time
from typing import Any, Dict, Optional



class MaskingFormatter(logging.Formatter):
    """
    Custom logging formatter that automatically redacts sensitive keywords,
    API keys, and authorization tokens from log records.
    """

    SENSITIVE_PATTERNS = [
        (re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE), "sk-***MASKED***"),
        (re.compile(r"(api[-_]?key|secret|password|token|authorization)\s*[:=]\s*['\"]?([^'\"\s]+)['\"]?", re.IGNORECASE), r"\1=***MASKED***"),
        (re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE), "Bearer ***MASKED***"),
    ]

    def format(self, record: logging.LogRecord) -> str:
        try:
            formatted = super().format(record)
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                formatted = pattern.sub(replacement, formatted)
            return formatted
        except Exception:
            # Fallback to standard formatting on unexpected error
            return super().format(record)


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

    try:
        telemetry_json = json.dumps(telemetry, default=str)
    except Exception as exc:
        telemetry_json = json.dumps({
            "event": "agent_execution",
            "agent": agent_name,
            "status": status,
            "serialization_warning": str(exc)
        })

    log_message = f"Agent [{agent_name}] status={status} time={execution_time_ms:.2f}ms | JSON: {telemetry_json}"
    
    if status == "SUCCESS":
        logger.info(log_message)
    elif status == "FALLBACK":
        logger.warning(log_message)
    else:
        logger.error(log_message)

