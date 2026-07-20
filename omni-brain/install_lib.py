import fitz

def extract_text(file_path):
    doc = fitz.open(file_path)

    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()

    return text