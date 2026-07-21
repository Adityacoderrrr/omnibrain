import asyncio
import json
from agents.state import AgentState
from agents.graph import supervisor_graph

async def run_test(scenario_name: str, question: str):
    print("=" * 60)
    print(f"SCENARIO: {scenario_name}")
    print(f"Question: {question}")
    print("-" * 60)
    
    state: AgentState = {
        "question": question,
        "document_id": "test-doc-id",
        "selected_agent": "",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": []
    }
    
    final_state = await supervisor_graph.ainvoke(state)
    
    print(f"Selected Agent: {final_state.get('selected_agent')}")
    print(f"SQL Query:      {final_state.get('sql_query')}")
    print(f"SQL Result:     {final_state.get('sql_result')}")
    print(f"Citations:      {json.dumps(final_state.get('citations'), indent=2)}")
    print(f"Response:       {final_state.get('response')}")
    print("Agent Trace:")
    for trace in final_state.get("agent_trace", []):
        print(f"  - {trace}")
    print("=" * 60 + "\n")

async def main():
    # Test all three routing paths in the workflow graph:
    # 1. Search path
    await run_test("Search RAG", "Explain the general summary paragraph in the text document context.")
    
    # 2. Vision path
    await run_test("Vision Multi-modal reasoning", "What does the line chart show on page 2?")
    
    # 3. SQL path
    await run_test("SQL database query", "What is the total revenue in the US database records?")

if __name__ == "__main__":
    asyncio.run(main())