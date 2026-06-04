"""
Email sending — supports two backends:

  1. Resend  (recommended) — free 3k/month, no-reply sender, no SMTP hassle
     Set in secrets.toml:  RESEND_API_KEY = "re_..."
     Sender will appear as:  ReportAI <onboarding@resend.dev>

  2. Gmail SMTP — any Gmail account works as sender
     Set in secrets.toml:  SENDER_EMAIL + SENDER_APP_PASSWORD
     Tip: create reportai.noreply@gmail.com so it looks like no-reply

The code tries Resend first, falls back to Gmail if not configured.
"""

import base64
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_PLACEHOLDERS = {
    "your-gmail@gmail.com", "xxxx xxxx xxxx xxxx",
    "your-email@gmail.com", "", "re_your_key_here",
}


def _get_secret(key: str) -> str:
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key, "")


# ── Resend backend ────────────────────────────────────────────────────────────

def _send_via_resend(
    recipient_email: str,
    subject: str,
    body: str,
    pdf_path: str,
    pptx_path: str,
) -> None:
    import resend

    api_key = _get_secret("RESEND_API_KEY")
    if not api_key or api_key in _PLACEHOLDERS:
        raise ValueError("RESEND_API_KEY not configured")

    resend.api_key = api_key

    # Build attachments list
    attachments = []
    for path in [pdf_path, pptx_path]:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            attachments.append({
                "filename": os.path.basename(path),
                "content": content,
            })

    resend.Emails.send({
        "from": "ReportAI <onboarding@resend.dev>",
        "to": [recipient_email],
        "subject": subject,
        "text": body,
        "attachments": attachments,
    })


# ── Gmail SMTP backend ────────────────────────────────────────────────────────

def _get_gmail_credentials() -> tuple[str, str]:
    email    = _get_secret("SENDER_EMAIL")
    password = _get_secret("SENDER_APP_PASSWORD")

    if not email or email in _PLACEHOLDERS:
        raise ValueError(
            "SENDER_EMAIL is not configured in secrets.toml.\n"
            "Either add RESEND_API_KEY (recommended) or SENDER_EMAIL + SENDER_APP_PASSWORD."
        )
    if not password or password in _PLACEHOLDERS or len(password.replace(" ", "")) < 12:
        raise ValueError(
            "SENDER_APP_PASSWORD is missing or still a placeholder.\n"
            "Get a 16-char App Password at myaccount.google.com/apppasswords"
        )
    return email, password


def _send_via_gmail(
    recipient_email: str,
    subject: str,
    body: str,
    pdf_path: str,
    pptx_path: str,
) -> None:
    sender_email, app_password = _get_gmail_credentials()

    msg = MIMEMultipart()
    msg["From"]    = f"ReportAI <{sender_email}>"
    msg["To"]      = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    for path in [pdf_path, pptx_path]:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(path)}"',
            )
            msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)


# ── Public function ───────────────────────────────────────────────────────────

def send_report(
    recipient_email: str,
    subject: str,
    body: str,
    pdf_path: str = "",
    pptx_path: str = "",
) -> str:
    """
    Send report email. Returns the backend used: 'resend' or 'gmail'.
    Tries Resend first, falls back to Gmail SMTP.
    Raises on failure.
    """
    resend_key = _get_secret("RESEND_API_KEY")
    if resend_key and resend_key not in _PLACEHOLDERS:
        _send_via_resend(recipient_email, subject, body, pdf_path, pptx_path)
        return "resend"
    else:
        _send_via_gmail(recipient_email, subject, body, pdf_path, pptx_path)
        return "gmail"
