from pathlib import Path


ALLOWED_DOC_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def extract_text_from_uploaded_document(file_obj) -> str:
    extension = Path(file_obj.name).suffix.lower()
    if extension not in ALLOWED_DOC_EXTENSIONS:
        raise ValueError("Unsupported file type. Allowed: .txt, .md, .pdf, .docx")

    if extension in {".txt", ".md"}:
        raw = file_obj.read()
        return raw.decode("utf-8", errors="ignore")

    if extension == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover
            raise ValueError("PDF parsing is unavailable. Install pypdf.") from exc
        reader = PdfReader(file_obj)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if extension == ".docx":
        try:
            from docx import Document
        except ImportError as exc:  # pragma: no cover
            raise ValueError("DOCX parsing is unavailable. Install python-docx.") from exc
        doc = Document(file_obj)
        return "\n".join(para.text for para in doc.paragraphs)

    return ""
