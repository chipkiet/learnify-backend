import io
import logging
import traceback
import fitz
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> dict:
    """
    Đọc PDF từ bytes (không cần file trên disk).
    Tương thích với cả local storage và Supabase Storage.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text = []

    for page in doc:
        page_text = page.get_text("text")
        pages_text.append(page_text)

    doc.close()

    return {
        "text": "\n\n".join(pages_text),
        "page_count": len(pages_text)
    }


def extract_text_from_docx(file_bytes: bytes) -> dict:
    """
    Đọc DOCX từ bytes.
    python-docx hỗ trợ file-like object trực tiếp.
    docx không có khái niệm rõ ràng về page_count như PDF.
    """
    file_obj = io.BytesIO(file_bytes)
    doc = DocxDocument(file_obj)
    lines = []

    from docx.oxml.ns import qn

    for child in doc.element.body:
        # Paragraph thường
        if child.tag == qn('w:p'):
            text = "".join(
                node.text for node in child.iter(qn('w:t'))
                if node.text
            )
            if text.strip():
                lines.append(text.strip())

        # Table — iterate từng row, từng cell
        elif child.tag == qn('w:tbl'):
            for row in child.iter(qn('w:tr')):
                cells = []
                for cell in row.iter(qn('w:tc')):
                    cell_text = "".join(
                        node.text for node in cell.iter(qn('w:t'))
                        if node.text
                    ).strip()
                    if cell_text:
                        cells.append(cell_text)
                if cells:
                    lines.append(" | ".join(cells))  # "col1 | col2 | col3"

    return {
        "text": "\n".join(lines),
        "page_count": 0,
    }


def extract_text_from_txt(file_bytes: bytes) -> dict:
    """
    Đọc TXT từ bytes.
    Thử UTF-8 trước, fallback sang latin-1 nếu có lỗi encoding.
    """
    try:
        text = file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        text = file_bytes.decode('latin-1')

    return {
        "text": text,
        "page_count": 0,
    }


EXTRACTORS = {
    'pdf': extract_text_from_pdf,
    'docx': extract_text_from_docx,
    'txt': extract_text_from_txt,
}


def extract_document(document) -> bool:
    """
    Nhận vào 1 Document instance.
    Tự động chọn extractor dựa theo file_type.

    Đọc file content qua Django Storage API (storage-agnostic):
    - Local dev  → FileSystemStorage  → đọc từ disk
    - Production → SupabaseStorage    → download từ Supabase bucket

    KHÔNG dùng document.file.path vì cloud storage không có local path.
    """
    from apps.documents.models import Document   # tránh circular import

    logger.info(f"[Extractor] Start — document_id={document.id}, type={document.file_type}")

    # Đánh dấu đang xử lý
    document.status = Document.Status.PROCESSING
    document.save(update_fields=['status'])

    try:
        extractor_fn = EXTRACTORS.get(document.file_type)

        if extractor_fn is None:
            raise ValueError(f"Không hỗ trợ loại file: {document.file_type}")

        # ── Đọc file bytes qua Django Storage API ──────────────────
        # document.file.open() hoạt động với mọi storage backend
        with document.file.open('rb') as f:
            file_bytes = f.read()

        result = extractor_fn(file_bytes)
        text   = result["text"].strip()

        # Ghi kết quả vào document
        document.extracted_text   = text
        document.word_count       = len(text.split())
        document.char_count       = len(text)
        document.page_count       = result["page_count"]
        document.status           = Document.Status.DONE
        document.extraction_error = None

        document.save(update_fields=[
            'extracted_text', 'word_count', 'char_count',
            'page_count', 'status', 'extraction_error',
        ])

        logger.info(
            f"[Extractor] Done — document_id={document.id} | "
            f"words={document.word_count} | chars={document.char_count} | "
            f"pages={document.page_count}"
        )
        return True

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"[Extractor] Failed — document_id={document.id} | error={e}")

        document.status = Document.Status.FAILED
        document.extraction_error = error_trace
        document.save(update_fields=['status', 'extraction_error'])
        return False
