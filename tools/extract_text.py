import sys
from pathlib import Path


def extract_text(file_path: str) -> str:
    """Return the full text content of a PDF, DOCX, or TXT file."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == '.pdf':
        return _extract_pdf(path)
    elif suffix == '.docx':
        return _extract_docx(path)
    elif suffix == '.txt':
        return _extract_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

def _extract_pdf(path: Path) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)

def _extract_docx(path: Path) -> str:
    from docx import Document
    doc = Document(path)
    return "\n".join(para.text for para in doc.paragraphs)

def _extract_txt(path: Path) -> str:
    return path.read_text(encoding='utf-8')
def extract_text_with_pages(file_path: str) -> list:
    """
    Return a list of (page_number, page_text) for PDFs.
    OCR fallback for scanned/image PDFs.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == '.pdf':
        import pdfplumber
        from pdf2image import convert_from_path
        import pytesseract

        pages = []

        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""

                # OCR fallback if no extractable text
                if not text.strip():
                    try:
                        images = convert_from_path(
                            str(path),
                            first_page=i,
                            last_page=i
                        )

                        if images:
                            text = pytesseract.image_to_string(images[0])

                    except Exception as e:
                        print(f"OCR failed on page {i}: {e}")

                pages.append((i, text))

        return pages

    else:
        # Non-PDF files
        return [(1, extract_text(file_path))]
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/extract_text.py <file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
    text = extract_text(file_path)
    print(text.replace('\ufeff', '').encode('utf-8', errors='replace').decode('utf-8'))