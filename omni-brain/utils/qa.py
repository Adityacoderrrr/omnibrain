import re


def summarize(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:3]) if sentences else "No text found in this PDF."
