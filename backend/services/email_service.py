import resend
import os

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "Zeusonic <no-reply@zeustechafrica.com>")


def send_otp_email(email: str, otp: str):
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY environment variable is not set")

    resend.api_key = RESEND_API_KEY

    html = (
        f"<h2>Verify your Zeusonic account</h2>"
        f"<p>Your verification code is:</p>"
        f"<div style='font-size: 28px; font-weight: bold; letter-spacing: 4px; margin: 24px 0;'>{otp}</div>"
        f"<p>This code expires in 10 minutes.</p>"
        f"<p style='color:#666; font-size: 12px;'>If you did not request this, ignore this email.</p>"
    )

    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [email],
            "subject": "Your Zeusonic verification code",
            "html": html,
        })
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")
