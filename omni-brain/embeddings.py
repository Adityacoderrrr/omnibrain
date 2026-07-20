from sentence_transformers import SentenceTransformer
import faiss

model = SentenceTransformer("all-MiniLM-L6-v2")

documents = []
index = faiss.IndexFlatL2(384)

def create_embeddings(text):

    chunks = []

    size = 500

    for i in range(0, len(text), size):
        chunks.append(text[i:i+size])

    vectors = model.encode(chunks)

    index.add(vectors)

    documents.extend(chunks)

    return len(chunks)