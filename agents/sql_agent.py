"""
SQL Agent component of the OmniBrain AI Intelligence Layer.
Translates user queries to SQL and runs them against a structured database.
"""

import json
import logging
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from .state import AgentState
from .prompts import SQL_AGENT_PROMPT, SQL_RESPONSE_PROMPT
from .llm import invoke_llm

logger = logging.getLogger("omnibrain.agents.sql_agent")


def get_sqlite_mock_engine():
    """
    Creates an in-memory SQLite engine populated with dummy records for testing/local fallbacks.
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
        # Commit transactions explicitly in sqlite
        conn.commit()
    logger.info("Initialized in-memory SQLite mock database.")
    return engine


def sql_agent(state: AgentState) -> AgentState:
    """
    SQL Agent node:
    - Generates a PostgreSQL/SQLite compatible SQL query from the natural language question.
    - Executes the query on the configured database or fallback mock database.
    - Summarizes query results and updates the state.

    Args:
        state (AgentState): Current execution state.

    Returns:
        AgentState: Updated execution state.
    """
    logger.info("SQL Agent triggered for query: '%s'", state.get("question"))
    settings = get_settings()

    question = state.get("question", "")
    if not question:
        state["response"] = "Error: Question is missing."
        state["agent_trace"] = ["SQL Agent: Failed - missing question"]
        return state

    try:
        # Step 1: Synthesize SQL Query
        sql_query = invoke_llm(prompt=f"Question: {question}", system_prompt=SQL_AGENT_PROMPT)
        
        # Clean query: strip markdown blocks if LLM output included them
        sql_query_clean = sql_query.replace("```sql", "").replace("```", "").strip()
        logger.info("Generated SQL Query: %s", sql_query_clean)

        # Step 2: Establish connection and run query
        if settings.database_url:
            logger.info("Connecting to external database configured at database_url.")
            engine = create_engine(settings.database_url)
        else:
            logger.warning("database_url not configured; using local in-memory SQLite engine.")
            engine = get_sqlite_mock_engine()

        with engine.connect() as conn:
            result = conn.execute(text(sql_query_clean))
            # Format rows
            rows = [dict(row._mapping) for row in result]
            sql_result_str = json.dumps(rows, default=str)
            logger.info("SQL Execution success. Retrieved %d rows.", len(rows))

        # Step 3: Summarize results using LLM
        summary_prompt = SQL_RESPONSE_PROMPT.format(
            question=question,
            query=sql_query_clean,
            results=sql_result_str
        )
        answer = invoke_llm(prompt=f"Question: {question}", system_prompt=summary_prompt)

        # Update State
        state["sql_query"] = sql_query_clean
        state["sql_result"] = sql_result_str
        state["response"] = answer
        state["citations"] = [{
            "page": 1,
            "source_type": "sql",
            "snippet": f"SQL Query: {sql_query_clean} | Results: {sql_result_str[:200]}"
        }]
        state["agent_trace"] = [
            f"SQL Agent: Generated SQL query: {sql_query_clean}",
            f"SQL Agent: Executed SQL query against database and formatted response"
        ]

    except Exception as exc:
        logger.exception("Error in SQL Agent node: %s", exc)
        state["response"] = "An error occurred during text-to-SQL execution or synthesis."
        state["sql_query"] = ""
        state["sql_result"] = ""
        state["citations"] = []
        state["agent_trace"] = [f"SQL Agent error: {str(exc)}"]

    return state
