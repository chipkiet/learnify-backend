"""
SMS Service — Abstraction layer gửi SMS OTP.

Provider hiện tại: eSMS (esms.vn) — phổ biến tại Việt Nam.
Để swap sang Twilio hoặc SpeedSMS, chỉ cần thay nội dung hàm _send_via_esms()
và cập nhật _send_sms() gọi đúng hàm provider mới.

API Reference: https://esms.vn/api-document
"""

import re
import requests
from django.conf import settings


class SMSError(Exception):
    """Raised khi gửi SMS thất bại."""
    pass


# ── Phone number normalization ─────────────────────────────────────────────────

def normalize_phone(phone: str) -> str:
    """
    Chuẩn hóa số điện thoại về dạng quốc tế không dấu '+'.
    VD: 0901234567 → 84901234567
        +84901234567 → 84901234567
    """
    phone = re.sub(r"\D", "", phone)  # Bỏ ký tự không phải số
    if phone.startswith("0"):
        phone = "84" + phone[1:]
    elif phone.startswith("+84"):
        phone = "84" + phone[3:]
    elif not phone.startswith("84"):
        phone = "84" + phone
    return phone


def is_valid_vietnamese_phone(phone: str) -> bool:
    """Kiểm tra số điện thoại Việt Nam hợp lệ (10 số bắt đầu bằng 0)."""
    clean = re.sub(r"\D", "", phone)
    if clean.startswith("84"):
        clean = "0" + clean[2:]
    return bool(re.match(r"^0[35789]\d{8}$", clean))


# ── eSMS provider ──────────────────────────────────────────────────────────────

def _send_via_esms(phone: str, message: str) -> None:
    """
    Gửi SMS qua eSMS API v4.
    SmsType = 2 → OTP (qua đầu số doanh nghiệp branded)
    """
    api_key    = settings.ESMS_API_KEY
    secret_key = settings.ESMS_SECRET_KEY
    brand_name = settings.ESMS_BRAND_NAME

    if not api_key or not secret_key:
        raise SMSError("eSMS chưa được cấu hình. Kiểm tra ESMS_API_KEY và ESMS_SECRET_KEY trong .env.")

    normalized_phone = normalize_phone(phone)

    payload = {
        "ApiKey":    api_key,
        "SecretKey": secret_key,
        "Phone":     normalized_phone,
        "Content":   message,
        "SmsType":   "2",          # 2 = OTP Brandname
        "Brandname": brand_name,
        "IsUnicode": "0",          # 0 = ASCII (đủ dùng cho OTP số)
    }

    try:
        response = requests.post(
            "https://rest.esms.vn/MainService.svc/json/SendMultipleMessage_V4_post_json/",
            json=payload,
            timeout=10,
        )
        data = response.json()

        # eSMS trả CodeResult = "100" khi thành công
        if str(data.get("CodeResult")) != "100":
            raise SMSError(
                f"eSMS error {data.get('CodeResult')}: {data.get('ErrorMessage', 'Unknown error')}"
            )
    except SMSError:
        raise
    except Exception as e:
        raise SMSError(f"Không thể kết nối eSMS: {e}")


# ── Public interface ───────────────────────────────────────────────────────────

def send_sms_otp(phone: str, otp_code: str) -> None:
    """
    Gửi mã OTP qua SMS.
    Đây là hàm duy nhất các service khác nên gọi — không gọi thẳng provider.
    """
    message = f"[Learnify] Ma xac thuc cua ban la: {otp_code}. Co hieu luc trong 10 phut. Khong chia se voi ai."
    _send_via_esms(phone, message)
