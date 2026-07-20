"""
LLM abstraction and mock fallback layer for OmniBrain agents.
"""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import get_settings

logger = logging.getLogger("omnibrain.agents.llm")


def get_llm() -> ChatOpenAI | None:
    """
    Get the LangChain ChatOpenAI instance if credentials are configured.
    """
    settings = get_settings()
    if settings.openai_api_key and settings.openai_api_key != "mock-key":
        try:
            return ChatOpenAI(
                openai_api_key=settings.openai_api_key,
                model="gpt-4o",
                temperature=0.0,
            )
        except Exception as exc:
            logger.error(f"Error initializing ChatOpenAI: {exc}")
    return None


def invoke_llm(prompt: str, system_prompt: str | None = None) -> str:
    """
    Invoke the LLM or route to a mock engine if OpenAI credentials are missing.
    """
    llm = get_llm()
    if llm:
        try:
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            response = llm.invoke(messages)
            return str(response.content).strip()
        except Exception as exc:
            logger.error(f"Error executing LLM call: {exc}. Falling back to mock.")

    # Fallback/Mock Response Generator
    logger.info("OpenAI API key missing or invalid; utilizing deterministic mock LLM.")
    
    prompt_lower = prompt.lower()
    sys_prompt_lower = (system_prompt or "").lower()

    # 1. Supervisor Routing Mock
    if "supervisor router" in sys_prompt_lower:
        import re
        if any(re.search(r"\b" + re.escape(word) + r"\b", prompt_lower) for word in ["image", "graph", "chart", "figure", "diagram"]):
            return "vision"
        elif any(re.search(r"\b" + re.escape(word) + r"\b", prompt_lower) for word in ["database", "sql", "table", "record", "sales", "revenue"]):
            return "sql"
        else:
            return "search"

    # 2. SQL Agent Query Generation Mock
    if "sql agent" in sys_prompt_lower and "select" in prompt_lower or "generate a valid postgresql compatible sql query" in sys_prompt_lower:
        return "SELECT SUM(revenue) FROM sales_records WHERE region = 'US';"

    # 3. SQL Agent Response Summary Mock
    if "executed sql query and its returned results" in sys_prompt_lower:
        return "According to the historical SQL database records, the total revenue in the US region is $150,000."

    # 4. Vision Agent Mock
    if "vision agent" in sys_prompt_lower:
        return "Based on the retrieved chart metadata on page 2, the revenue shows an upward trend reaching $150,000."

    # 5. Search Agent Mock
    if "search agent" in sys_prompt_lower:
        # Extract snippet or use default mock answer
        return "Based on the retrieved text context, the document states that revenue grew by 15% year-over-year."

    return "Mock Response: External LLM dependency is not configured."
