from pathlib import Path


class TextExtractor:
    """Handles text extraction from PDF, DOCX, and TXT documents."""

    def extract_text(self, file_path: str) -> str:
        """Return the full text content of a supported document."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return self._extract_pdf(path)
        elif suffix == ".docx":
            return self._extract_docx(path)
        elif suffix == ".txt":
            return self._extract_txt(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def extract_text_with_pages(self, file_path: str) -> list:
        """Return page-by-page extracted text with OCR fallback for PDFs."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            import pdfplumber
            from pdf2image import convert_from_path
            import pytesseract

            pages = []

            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""

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

        return [(1, self.extract_text(file_path))]

    def _extract_pdf(self, path: Path) -> str:
        import pdfplumber

        text_parts = []

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text_parts.append(page_text)

        return "\n".join(text_parts)

    def _extract_docx(self, path: Path) -> str:
        from docx import Document

        doc = Document(path)
        return "\n".join(para.text for para in doc.paragraphs)

    def _extract_txt(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")