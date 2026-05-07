"""File operation tools — resume parsing and report export."""

import json
from pathlib import Path
from hirehive.config import config
from hirehive.utils.text import extract_email, extract_phone


def parse_resume_pdf(file_path: str) -> dict:
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        text = f"[pypdf not installed — cannot parse {file_path}]"
    except Exception as e:
        return {"error": str(e), "file_path": file_path}

    return _parse_text(text, file_path)


def parse_resume_docx(file_path: str) -> dict:
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        text = f"[python-docx not installed — cannot parse {file_path}]"
    except Exception as e:
        return {"error": str(e), "file_path": file_path}

    return _parse_text(text, file_path)


def _parse_text(text: str, file_path: str) -> dict:
    return {
        "file_path": file_path,
        "raw_text": text,
        "extracted_email": extract_email(text),
        "extracted_phone": extract_phone(text),
        "char_count": len(text),
    }


def read_user_resume() -> dict:
    from hirehive.storage import resume_repo
    row = resume_repo.get_active_resume()
    if not row:
        return {"error": "No resume uploaded. Use 'resume upload' first."}
    return {"id": row["id"], "file_path": row["file_path"], "raw_text": row["raw_text"]}


def export_report_markdown(content: str, filename: str) -> dict:
    export_dir = config.data_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    filepath = export_dir / filename
    filepath.write_text(content, encoding="utf-8")
    return {"path": str(filepath), "size": len(content)}


def export_report_json(content: dict, filename: str) -> dict:
    export_dir = config.data_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    filepath = export_dir / filename
    filepath.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": str(filepath), "keys": list(content.keys()) if isinstance(content, dict) else "array"}
