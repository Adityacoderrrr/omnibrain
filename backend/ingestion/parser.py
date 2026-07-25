# ingestion/parser.py

from unstructured.partition.pdf import partition_pdf
import os

def parse_financial_document(file_path: str, output_image_dir: str = "../data/extracted_images/"):
    """
    Dissects a PDF into text, tables (HTML), and images.
    """
    # Ensure the output directory exists
    os.makedirs(output_image_dir, exist_ok=True)

    print(f"Starting high-res partition of {file_path}...")
    
    # The Unstructured vision model extraction
    elements = partition_pdf(
        filename=file_path,
        strategy="hi_res",
        infer_table_structure=True, 
        extract_images_in_pdf=True,
        extract_image_block_output_dir=output_image_dir
    )

    texts, tables, images = [], [], []

    # Sort the extracted elements into our three buckets
    for el in elements:
        if el.category == "Table":
            tables.append({
                "html": el.metadata.text_as_html, 
                "page": el.metadata.page_number
            })
        elif el.category == "Image":
            images.append({
                "path": el.metadata.image_path, 
                "page": el.metadata.page_number
            })
        elif el.category in ["NarrativeText", "Title", "ListItem"]:
            texts.append({
                "text": el.text, 
                "page": el.metadata.page_number
            })
            
    print(f"Extracted: {len(texts)} text blocks, {len(tables)} tables, {len(images)} images.")
    
    # Return the buckets so embedder.py can process them next
    return texts, tables, images