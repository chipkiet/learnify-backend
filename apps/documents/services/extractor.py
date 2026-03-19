import logging
import traceback
import fitz 
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> dict :
    doc = fitz.open(file_path)
    pages_text = []
    
    for page in doc : 
        page_text = page.get_text("text")
        pages_text.append(page_text)
        
    doc.close()
    
    return {
        "text": "\n\n".join(pages_text),    #ngăn cách rõ ràng giữa các trang với nhau
        "page_count": len(pages_text)
    }

def extract_text_from_docx(file_path: str) -> dict :
    """ 
        docx không có khái niệm rõ ràng về page_count như PDF
        -> đến số section breaks làm ước lượng
        vấn đề trước đây, docx không đọc được các dữ liệu trong bảng
        (doc.paragraph), ta nên fix thêm cơ chế cho đọc table nữa )
    """
    
    doc = DocxDocument(file_path)
    lines = []
    
    # ── Duyệt theo thứ tự xuất hiện trong document ──────
    # doc.element.body chứa tất cả: paragraph + table đúng thứ tự
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
                    lines.append(" | ".join(cells))  # "1 | happy | vui vẻ | She is happy"

    return {
        "text": "\n".join(lines),
        "page_count": 0,
    }
    
    
    
def extract_text_from_txt(file_path: str) -> dict :
    """ 
        Thử UTF8 trước, sau đó fallback sang latin nếu có lỗi encoding
    """
    
    try :
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f :
            text = f.read()
        
    return {
        "text" : text,
        "page_count" : 0,
    }
    
EXTRACTORS = {
    'pdf': extract_text_from_pdf,
    'docx' : extract_text_from_docx,
    'txt': extract_text_from_txt
}
def extract_document(document) -> bool:
    """
    Nhận vào 1 Document instance.
    Tự động chọn extractor dựa theo file_type.
    Cập nhật tất cả fields và save().
    Trả về True nếu thành công, False nếu thất bại.
    """
    from apps.documents.models import Document   # tránh circular import

    logger.info(f"[Extractor] Start — document_id={document.id}, type={document.file_type}")

    # Đánh dấu đang xử lý
    document.status = Document.Status.PROCESSING
    document.save(update_fields=['status'])

    try:
        file_path = document.file.path
        extractor_fn = EXTRACTORS.get(document.file_type)

        if extractor_fn is None:
            raise ValueError(f"Nỏ hỗ trợ loại file type: {document.file_type} này đâu bé ơi !")

        result = extractor_fn(file_path)
        text   = result["text"].strip()

        # Ghi kết quả vào document
        document.extracted_text = text
        document.word_count     = len(text.split())
        document.char_count     = len(text)
        document.page_count     = result["page_count"]
        document.status         = Document.Status.DONE
        document.extraction_error = None          # xóa lỗi cũ nếu có

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
        document.extraction_error = error_trace   # lưu full traceback để debug
        document.save(update_fields=['status', 'extraction_error'])
        return False
