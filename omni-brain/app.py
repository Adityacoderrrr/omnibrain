from fastapi import FastAPI, UploadFile, File
import shutil
import os

from utils.parser import extract_text
from utils.embeddings import create_embeddings
from utils.qa import summarize

app = FastAPI(title="OmniBrain")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text(filepath)

    create_embeddings(text)

    summary = summarize(text)

    return {
        "filename": file.filename,
        "summary": summary
    }
    