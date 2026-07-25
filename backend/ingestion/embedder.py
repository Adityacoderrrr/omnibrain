# ingestion/embedder.py

import os
import base64
from PIL import Image
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer

# 1. Initialize Hugging Face Serverless Client (requires free HF_TOKEN)
hf_client = InferenceClient(api_key=os.getenv("HF_TOKEN"))

# 2. Local CLIP for tiny, fast visual embeddings (512 dimensions)
clip_model = SentenceTransformer('clip-ViT-B-32')

# Define HF models for serverless execution
TEXT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
VISION_MODEL = "Qwen/Qwen2-VL-7B-Instruct"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def process_texts(texts: list[dict]) -> list[dict]:
    if not texts:
        return []

    print(f"Embedding {len(texts)} text blocks via Hugging Face API...")
    processed = []
    
    for item in texts:
        # Calls HF Serverless API for embeddings
        embedding = hf_client.feature_extraction(
            text=item["text"], 
            model=EMBEDDING_MODEL
        )
        
        processed.append({
            "vector": {
                "text": embedding.tolist()
            },
            "payload": {
                "element_type": "text",
                "content": item["text"],
                "page_number": item["page"]
            }
        })
    return processed

def process_tables(tables: list[dict]) -> list[dict]:
    if not tables:
        return []

    print(f"Summarizing and embedding {len(tables)} tables via HF Mistral API...")
    processed = []
    
    for item in tables:
        table_html = item["html"]
        if not table_html:
            continue

        prompt = (
            "Analyze the following HTML table from a financial document. "
            "Provide a detailed, structured Markdown summary highlighting "
            "key financial metrics, numerical values, and trends.\n\n"
            f"Table HTML:\n{table_html}"
        )
        
        # 1. Summarize via Hugging Face Chat API
        response = hf_client.chat_completion(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        summary = response.choices[0].message.content

        # 2. Embed the summary via HF API
        embedding = hf_client.feature_extraction(
            text=summary, 
            model=EMBEDDING_MODEL
        )

        processed.append({
            "vector": {
                "text": embedding.tolist()
            },
            "payload": {
                "element_type": "table",
                "content": summary,
                "raw_html": table_html,
                "page_number": item["page"]
            }
        })
    return processed

def process_images(images: list[dict]) -> list[dict]:
    if not images:
        return []

    print(f"Processing {len(images)} images via HF Qwen Vision API...")
    processed = []

    for item in images:
        image_path = item["path"]
        if not os.path.exists(image_path):
            continue

        base64_img = encode_image_to_base64(image_path)

        # 1. Generate caption via Hugging Face Vision API
        vlm_response = hf_client.chat_completion(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this financial graphic or chart in detail. Extract all axes, legends, numbers, and key takeaways."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]
                }
            ],
            max_tokens=500
        )
        caption = vlm_response.choices[0].message.content

        # 2. Text embedding via HF API
        text_vector = hf_client.feature_extraction(
            text=caption, 
            model=EMBEDDING_MODEL
        ).tolist()

        # 3. Visual embedding via local lightweight CLIP
        pil_img = Image.open(image_path)
        clip_vector = clip_model.encode(pil_img).tolist()

        processed.append({
            "vector": {
                "text": text_vector,
                "image": clip_vector
            },
            "payload": {
                "element_type": "image",
                "content": caption,
                "image_path": image_path,
                "page_number": item["page"]
            }
        })
    return processed