"""
Utility module for the OmniBrain AI Intelligence Layer.

Provides resilience patterns (retries with exponential backoff), execution measurement timers,
prompt sanitization, safe JSON parsing, and token estimation helpers.
"""

import functools
import json
import logging
import re
import time
from typing import Any, Callable, Dict, Tuple, Type, TypeVar

logger = logging.getLogger("omnibrain.agents.utils")

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable[[F], F]:
    """
    Decorator that applies exponential backoff retries to a function or method.

    Args:
        max_retries (int): Maximum number of attempts before raising exception.
        backoff_factor (float): Multiplier for sleep duration between attempts.
        exceptions (Tuple[Type[Exception], ...]): Tuple of exception classes to catch and retry.

    Returns:
        Callable: Wrapped function with retry logic.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = 0.5
            last_exception: Exception | None = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    logger.warning(
                        "Attempt %d/%d failed for function '%s': %s. Retrying in %.2fs...",
                        attempt, max_retries, func.__name__, exc, delay
                    )
                    if attempt == max_retries:
                        break
                    time.sleep(delay)
                    delay *= backoff_factor

            logger.error("Function '%s' exhausted all %d retries.", func.__name__, max_retries)
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Execution failed after {max_retries} attempts.")

        return wrapper  # type: ignore

    return decorator


class ExecutionTimer:
    """
    Context manager for measuring code execution latency in milliseconds.
    """

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "ExecutionTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0


def estimate_token_count(text: str) -> int:
    """
    Estimates the number of tokens in a string using standard word/subword heuristic ratio.

    Args:
        text (str): Input text string.

    Returns:
        int: Estimated token count (roughly ~4 characters per token for English).
    """
    if not text:
        return 0
    return max(1, int(len(text) / 4))


def parse_json_safely(text: str, default: Any = None) -> Any:
    """
    Safely parses JSON from text strings, handling markdown block wrappers (```json ... ```)
    or trailing invalid characters.

    Args:
        text (str): String containing raw text or JSON.
        default (Any): Default return value if parsing fails.

    Returns:
        Any: Decoded JSON object (dict/list) or default value if parsing fails.
    """
    if not text or not isinstance(text, str):
        return default if default is not None else {}

    cleaned = text.strip()
    
    # Strip markdown code fencing if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: find first '{' or '[' and last '}' or ']'
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        logger.warning("Failed to parse JSON string: '%s'", cleaned[:100])
        return default if default is not None else {}


def sanitize_prompt_input(text: str, max_length: int = 4096) -> str:
    """
    Sanitizes user input string to prevent control character injection and limit string length.

    Args:
        text (str): Input string.
        max_length (int): Upper bound character limit.

    Returns:
        str: Sanitized, trimmed string.
    """
    if not text:
        return ""
    # Strip null bytes and control characters (except standard whitespace/newlines)
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return sanitized.strip()[:max_length]
