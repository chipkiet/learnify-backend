"""
Supabase Storage Backend cho Django.

Thay thế local FileSystemStorage để lưu media files (PDF, DOCX, ...)
lên Supabase Storage bucket thay vì disk của server (Render ephemeral filesystem).

Upload  → supabase.storage.from_(bucket).upload(path, file_bytes)
Download → supabase.storage.from_(bucket).create_signed_url(path, expires_in)
Delete  → supabase.storage.from_(bucket).remove([path])
"""

import os
from io import BytesIO
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from supabase import create_client, Client


def _get_supabase_client() -> Client:
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_SERVICE_KEY
    return create_client(url, key)


class SupabaseStorage(Storage):
    """
    Django Storage backend sử dụng Supabase Storage.
    Cấu hình qua settings:
        SUPABASE_URL        = "https://<project>.supabase.co"
        SUPABASE_SERVICE_KEY = "<service_role key>"
        SUPABASE_BUCKET     = "learnify-media"
    """

    def __init__(self):
        self.client: Client = _get_supabase_client()
        self.bucket: str = settings.SUPABASE_BUCKET

    # ──────────────────────────────────────────────────────────
    # Core: _save / _open / delete / exists / url
    # ──────────────────────────────────────────────────────────

    def _save(self, name: str, content) -> str:
        """Upload file lên Supabase Storage, trả về path đã lưu."""
        file_bytes = content.read()
        content_type = getattr(content, "content_type", "application/octet-stream")

        # Supabase không tự tạo folder → path là key (vd: "documents/2024/05/01/file.pdf")
        self.client.storage.from_(self.bucket).upload(
            path=name,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return name

    def _open(self, name: str, mode: str = "rb"):
        """Download file từ Supabase về dưới dạng ContentFile."""
        response = self.client.storage.from_(self.bucket).download(name)
        return ContentFile(response, name=name)

    def delete(self, name: str) -> None:
        """Xóa file khỏi Supabase Storage."""
        try:
            self.client.storage.from_(self.bucket).remove([name])
        except Exception:
            pass  # Bỏ qua nếu file không tồn tại

    def exists(self, name: str) -> bool:
        """Kiểm tra file có tồn tại không."""
        try:
            # list files tại parent path, check tên file
            parts = name.rsplit("/", 1)
            folder = parts[0] if len(parts) > 1 else ""
            filename = parts[-1]
            files = self.client.storage.from_(self.bucket).list(folder)
            return any(f.get("name") == filename for f in (files or []))
        except Exception:
            return False

    def url(self, name: str) -> str:
        """
        Trả về signed URL có hiệu lực 1 giờ (3600 giây).
        Bucket là private nên cần signed URL thay vì public URL.
        """
        try:
            response = self.client.storage.from_(self.bucket).create_signed_url(
                path=name,
                expires_in=3600,
            )
            return response.get("signedURL", "")
        except Exception:
            return ""

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────

    def size(self, name: str) -> int:
        """Trả về kích thước file (bytes). Không thiết yếu nhưng hữu ích."""
        try:
            parts = name.rsplit("/", 1)
            folder = parts[0] if len(parts) > 1 else ""
            filename = parts[-1]
            files = self.client.storage.from_(self.bucket).list(folder)
            for f in (files or []):
                if f.get("name") == filename:
                    return f.get("metadata", {}).get("size", 0)
        except Exception:
            pass
        return 0

    def get_available_name(self, name: str, max_length=None) -> str:
        """
        Ghi đè file nếu đã tồn tại (upsert=true ở _save).
        Không cần thêm suffix như FileSystemStorage mặc định.
        """
        return name
