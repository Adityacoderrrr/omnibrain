from transformers import pipeline

summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

def summarize(text):

    text = text[:3000]

    result = summarizer(
        text,
        max_length=150,
        min_length=50,
        do_sample=False
    )

    return result[0]["summary_text"]