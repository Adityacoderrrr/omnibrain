"""
SQL Agent component of the OmniBrain AI Intelligence Layer.
Translates natural language questions to read-only SQL, executes queries against target database, and synthesizes findings.
"""

import json
import re
from typing import List, Dict, Any
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from agents.state import AgentState
from agents.prompts import SQL_AGENT_PROMPT, SQL_RESPONSE_PROMPT
from agents.llm import invoke_llm
from agents.logger import get_logger, log_agent_execution
from agents.utils import ExecutionTimer, sanitize_prompt_input

logger = get_logger("omnibrain.agents.sql_agent")


def get_sqlite_mock_engine():
    """
    Creates an in-memory SQLite database populated with sales records for local testing/fallbacks.
    """
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE sales_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                region VARCHAR(50),
                product VARCHAR(100),
                revenue NUMERIC,
                units_sold INTEGER,
                margin NUMERIC
            );
        """))
        conn.execute(text("""
            INSERT INTO sales_records (date, region, product, revenue, units_sold, margin) VALUES
            ('2026-01-10', 'US', 'Cloud Subscription', 50000, 100, 0.82),
            ('2026-02-15', 'US', 'Professional Services', 100000, 50, 0.45),
            ('2026-03-01', 'EU', 'Cloud Subscription', 40000, 80, 0.80),
            ('2026-04-12', 'APAC', 'Hardware Appliances', 30000, 15, 0.30);
        """))
        conn.commit()
    logger.info("Initialized in-memory SQLite mock database.")
    return engine


def validate_sql_safety(query: str) -> bool:
    """
    Validates that generated SQL query is strictly read-only SELECT or WITH statement.
    Prevents SQL injection of destructive DDL/DML statements.

    Args:
        query (str): SQL query string.

    Returns:
        bool: True if safe read-only query, False otherwise.
    """
    clean = query.strip().upper()
    if not (clean.startswith("SELECT") or clean.startswith("WITH")):
        return False

    disallowed_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "EXEC", "MERGE"]
    for keyword in disallowed_keywords:
        if re.search(r"\b" + keyword + r"\b", clean):
            return False
    return True


def sql_agent(state: AgentState) -> Dict[str, Any]:
    """
    SQL Agent node:
    - Generates read-only SQL query from natural language user question.
    - Validates safety to block destructive DDL/DML operations.
    - Executes query on database URL or fallback in-memory SQLite engine.
    - Summarizes dataset results and updates AgentState.

    Args:
        state (AgentState): Current execution state.

    Returns:
        Dict[str, Any]: Partial state update.
    """
    with ExecutionTimer() as timer:
        question = sanitize_prompt_input(state.get("question", ""))
        logger.info("SQL Agent triggered for query: '%s'", question)

        settings = get_settings()

        if not question:
            return {
                "response": "Error: Question is missing.",
                "sql_query": "",
                "sql_result": "",
                "citations": [],
                "agent_responses": {},
                "agent_trace": ["SQL Agent: Failed - missing question"]
            }

        try:
            # Step 1: Synthesize SQL Query
            raw_sql = invoke_llm(prompt=f"Question: {question}", system_prompt=SQL_AGENT_PROMPT)
            sql_query_clean = re.sub(r"^```(?:sql)?\s*|\s*```$", "", raw_sql, flags=re.IGNORECASE).strip()
            logger.info("Generated SQL Query: %s", sql_query_clean)

            # Step 2: Validate SQL Safety
            if not validate_sql_safety(sql_query_clean):
                logger.error("SQL safety validation failed for query: '%s'", sql_query_clean)
                raise ValueError("Generated SQL contains unsafe or non-SELECT instructions.")

            # Step 3: Execute SQL Query
            if settings.database_url:
                logger.info("Connecting to external database configured at database_url.")
                engine = create_engine(settings.database_url)
            else:
                logger.warning("database_url unconfigured; using local in-memory SQLite engine.")
                engine = get_sqlite_mock_engine()

            with engine.connect() as conn:
                result = conn.execute(text(sql_query_clean))
                if getattr(result, "returns_rows", True):
                    rows = [dict(row._mapping) for row in result]
                else:
                    rows = [{"affected_rows": getattr(result, "rowcount", 0)}]
                sql_result_str = json.dumps(rows, default=str)
                logger.info("SQL Execution success. Retrieved %d rows.", len(rows))

            # Step 4: Summarize Results via LLM
            summary_prompt = SQL_RESPONSE_PROMPT.format(
                question=question,
                query=sql_query_clean,
                results=sql_result_str
            )
            answer = invoke_llm(prompt=f"Question: {question}", system_prompt=summary_prompt)

            log_agent_execution(
                logger=logger,
                agent_name="sql",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="SUCCESS",
                extra_metadata={"rows_retrieved": len(rows), "sql_query": sql_query_clean}
            )

            return {
                "sql_query": sql_query_clean,
                "sql_result": sql_result_str,
                "response": answer,
                "citations": [{
                    "page": 1,
                    "source_type": "sql",
                    "snippet": f"SQL Query: {sql_query_clean} | Results: {sql_result_str[:200]}"
                }],
                "agent_responses": {"sql": answer},
                "agent_trace": [
                    f"SQL Agent: Generated safe query: {sql_query_clean}",
                    f"SQL Agent: Executed query and formatted response ({len(rows)} records retrieved)"
                ]
            }

        except Exception as exc:
            logger.exception("Error in SQL Agent node: %s", exc)
            log_agent_execution(
                logger=logger,
                agent_name="sql",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="FAILED",
                extra_metadata={"error": str(exc)}
            )

            return {
                "response": "An error occurred during text-to-SQL query generation or execution.",
                "sql_query": "",
                "sql_result": "",
                "citations": [],
                "agent_responses": {},
                "agent_trace": [f"SQL Agent error: {str(exc)}"]
            }
