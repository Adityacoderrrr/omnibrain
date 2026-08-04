"""
Unit tests for OmniBrain Configuration, Structured Logging, and Utility modules.
"""

import pytest
import logging
from app.core.config import get_settings, Settings, clear_settings_cache
from agents.logger import get_logger, log_agent_execution
from agents.utils import (
    with_retry,
    ExecutionTimer,
    estimate_token_count,
    parse_json_safely,
    sanitize_prompt_input
)


def test_settings_singleton_and_masking():
    """Verify Settings initializes with defaults and correctly masks sensitive credentials."""
    settings = get_settings()
    assert settings.app_env in ["development", "production", "test"]
    assert settings.qdrant_text_collection == "omnibrain_text"

    masked = settings.to_dict_masked()
    if settings.openai_api_key:
        assert "***" in masked["openai_api_key"]
    assert "openai_api_key" in masked


def test_clear_settings_cache():
    """Verify clear_settings_cache successfully invalidates LRU cache."""
    s1 = get_settings()
    clear_settings_cache()
    s2 = get_settings()
    assert s1 is not s2



def test_logger_creation_and_execution_logging(capsys):
    """Verify custom logger creation and telemetry step formatting."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)

    log_agent_execution(
        logger=logger,
        agent_name="test_agent",
        query="What is sales revenue?",
        execution_time_ms=123.45,
        status="SUCCESS",
        extra_metadata={"test": "val"}
    )
    captured = capsys.readouterr()
    assert "test_agent" in captured.out
    assert "123.45ms" in captured.out


def test_utils_execution_timer():
    """Verify ExecutionTimer measures elapsed duration in milliseconds."""
    import time
    with ExecutionTimer() as timer:
        time.sleep(0.01)
    assert timer.elapsed_ms >= 8.0  # At least ~8ms accounting for OS timer resolution


def test_utils_estimate_token_count():
    """Verify token count heuristic estimation."""
    assert estimate_token_count("") == 0
    assert estimate_token_count("Hello world") >= 1
    assert estimate_token_count("A" * 100) == 25


def test_utils_parse_json_safely():
    """Verify parsing valid JSON, markdown-wrapped JSON, and fallback cases."""
    # Standard JSON
    assert parse_json_safely('{"key": "value"}') == {"key": "value"}

    # Markdown wrapped JSON
    markdown_json = """```json
    {
        "agent": "sql",
        "confidence": 0.95
    }
    ```"""
    res = parse_json_safely(markdown_json)
    assert res.get("agent") == "sql"

    # Invalid string fallback
    assert parse_json_safely("Invalid JSON string", default={"fallback": True}) == {"fallback": True}


def test_utils_sanitize_prompt_input():
    """Verify prompt sanitization strips null bytes and enforces character bounds."""
    raw_prompt = "  Hello \x00 world!  "
    sanitized = sanitize_prompt_input(raw_prompt, max_length=10)
    assert "\x00" not in sanitized
    assert len(sanitized) <= 10


def test_utils_with_retry_success_and_failure():
    """Verify with_retry decorator retries on exception and succeeds or raises on exhaustion."""
    call_count = 0

    @with_retry(max_retries=3, backoff_factor=1.1, exceptions=(ValueError,))
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Transient error")
        return "Success"

    assert flaky_func() == "Success"
    assert call_count == 2

    # Exhaustion case
    call_count_fail = 0

    @with_retry(max_retries=2, backoff_factor=1.1, exceptions=(TypeError,))
    def failing_func():
        nonlocal call_count_fail
        call_count_fail += 1
        raise TypeError("Persistent failure")

    with pytest.raises(TypeError):
        failing_func()
    assert call_count_fail == 2


def test_safe_env_parsing(monkeypatch):
    """Verify _safe_int and _safe_float fall back gracefully when given invalid string values."""
    from app.core.config import _safe_int, _safe_float
    monkeypatch.setenv("TEST_BAD_INT", "not_an_int")
    monkeypatch.setenv("TEST_BAD_FLOAT", "not_a_float")

    assert _safe_int("TEST_BAD_INT", 8000) == 8000
    assert _safe_float("TEST_BAD_FLOAT", 10.0) == 10.0


def test_logger_masking_sensitive_patterns(capsys):
    """Verify MaskingFormatter redacts secret API keys and bearer tokens from logs."""
    from agents.logger import get_logger
    test_log = get_logger("secret_test_logger")
    test_log.info("Connecting with api_key=sk-1234567890123456789012345678 and Authorization: Bearer secret_token_xyz")
    captured = capsys.readouterr()
    assert "sk-1234567890123456789012345678" not in captured.out
    assert "***MASKED***" in captured.out

