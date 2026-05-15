import random
import string
import resend
from datetime import timedelta
from django.conf import settings
from django.utils import timezone


OTP_EXPIRE_MINUTES = 10


def generate_otp(user, purpose: str) -> str:
    """
    Generate a 6-digit OTP, persist it to the user record, and return the code.
    Overwrites any existing OTP — calling this again invalidates the previous one.
    """
    code = "".join(random.choices(string.digits, k=6))

    user.otp_code = code
    user.otp_expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    user.otp_purpose = purpose
    user.save(update_fields=["otp_code", "otp_expires_at", "otp_purpose"])

    return code


def send_otp_email(user, otp_code: str, purpose: str) -> None:
    """
    Send an OTP email via Resend API.
    Purpose controls the email subject and messaging.
    """
    resend.api_key = settings.RESEND_API_KEY

    if purpose == "verify_email":
        subject = "Xác thực email Learnify của bạn"
        action_text = "xác thực địa chỉ email"
    else:  # reset_password
        subject = "Đặt lại mật khẩu Learnify"
        action_text = "đặt lại mật khẩu"

    display_name = user.full_name or user.email.split("@")[0]
    html_body = _build_otp_email_html(display_name, otp_code, action_text, purpose)

    resend.Emails.send({
        "from": settings.RESEND_FROM_EMAIL,
        "to": [user.email],
        "subject": subject,
        "html": html_body,
    })


def _build_otp_email_html(display_name: str, otp_code: str, action_text: str, purpose: str) -> str:
    """Return a branded HTML email containing the OTP code."""
    return f"""
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Learnify OTP</title>
</head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:16px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,0.08);max-width:560px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="background:#d97757;padding:32px 40px;text-align:center;">
              <span style="font-size:28px;font-weight:800;color:#ffffff;
                           font-family:'Georgia',serif;letter-spacing:-0.5px;">
                Learnify
              </span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <p style="margin:0 0 8px;font-size:22px;font-weight:700;color:#1a1a1a;">
                Xin chào, {display_name}!
              </p>
              <p style="margin:0 0 28px;font-size:15px;color:#555;line-height:1.6;">
                Bạn đã yêu cầu {action_text}.<br/>
                Sử dụng mã OTP dưới đây — mã sẽ hết hạn sau <strong>{OTP_EXPIRE_MINUTES} phút</strong>.
              </p>

              <!-- OTP Box -->
              <div style="background:#fdf6f3;border:2px solid #d97757;border-radius:12px;
                          padding:28px;text-align:center;margin-bottom:28px;">
                <p style="margin:0 0 8px;font-size:12px;font-weight:700;color:#d97757;
                           letter-spacing:2px;text-transform:uppercase;">Mã xác thực</p>
                <p style="margin:0;font-size:44px;font-weight:800;color:#1a1a1a;
                           letter-spacing:10px;font-family:'Courier New',monospace;">
                  {otp_code}
                </p>
              </div>

              <p style="margin:0;font-size:13px;color:#888;line-height:1.6;">
                Nếu bạn không yêu cầu điều này, hãy bỏ qua email này. Tài khoản của
                bạn vẫn an toàn.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#faf9f7;padding:20px 40px;border-top:1px solid #e8e4de;">
              <p style="margin:0;font-size:12px;color:#aaa;text-align:center;">
                © {timezone.now().year} Learnify &nbsp;·&nbsp;
                <a href="https://learnify.info.vn" style="color:#d97757;text-decoration:none;">
                  learnify.info.vn
                </a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
