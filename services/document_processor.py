import re
import os
import pytesseract
from tools.extract_text import extract_text_with_pages

class DocumentProcessor:
    """Handles document text extraction, cleaning, and preprocessing."""

    def __init__(self):
        tesseract_path = os.getenv("TESSERACT_PATH")
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def clean_pages(self, page_texts):
        """Clean extracted page text by removing formatting noise and normalising whitespace."""

        clean_page_texts = []
        for page_num, page in page_texts:
            cleaned = re.sub(r'-\n', '', page)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            clean_page_texts.append((page_num, cleaned))

        return clean_page_texts

    def process_document(self, file_path):
        """Extract, clean, and combine document text for downstream analysis."""

        page_texts = extract_text_with_pages(str(file_path))
        clean_page_texts = self.clean_pages(page_texts)
        clean_text = "\n".join([t for _, t in clean_page_texts])

        return clean_page_texts, clean_text