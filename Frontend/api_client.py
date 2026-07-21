import time

def send_query_to_orchestrator(query: str, config: dict):
    # 1. Define the fake steps the "kitchen" would normally take
    steps = [
        ("Supervisor routing query...", "Analyzing intent to select specialized agents."),
        ("Parsing complex tables using VLM...", "Extracting metrics from embedded images."),
        (f"Querying Vector DB...", "Found 3 relevant paragraphs."),
        ("Running NeMo Guardrails check...", "Output verified. No hallucinations detected.")
    ]
    
    # 2. Simulate the Waiter giving live updates to the Customer
    for status_text, detail in steps:
        time.sleep(1.5)  
        yield {"type": "status", "label": status_text, "detail": detail}
        
    # 3. Simulate the Waiter bringing out the final meal
    time.sleep(1)
    yield {
        "type": "final_result",
        "memo": f"**Analysis Complete for query:** '{query}'\n\nAll metrics indicate a strong upward trend.",
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=600",
        "logs": {"toxicity_score": 0.00, "context_grounding": 0.98}
    }