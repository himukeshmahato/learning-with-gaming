import fitz
import re

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print("PDF reading error:", e)
        return ""

    # Clean text to avoid huge newline gaps and multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def chunk_text(text, max_chars=3000):
    chunks = []
    # simple chunking by characters for minor project needs
    for i in range(0, len(text), max_chars):
        chunks.append(text[i:i+max_chars])
    return chunks
