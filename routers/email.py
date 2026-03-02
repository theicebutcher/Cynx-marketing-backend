import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from auth import validate_token

router = APIRouter()


class SendEmailRequest(BaseModel):
    to: List[str]
    subject: str
    html: str


@router.post("/send")
async def send_email(
    req: SendEmailRequest,
    authorization: Optional[str] = Header(None),
):
    await validate_token(authorization)

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    secure = os.getenv("SMTP_SECURE", "false").lower() == "true"
    from_name = os.getenv("SMTP_FROM_NAME", "")
    from_email = os.getenv("SMTP_FROM_EMAIL") or user

    if not host or not user or not password:
        raise HTTPException(status_code=500, detail="SMTP not configured on server. Set SMTP_HOST, SMTP_USER, SMTP_PASS in api/.env")

    results = []
    for recipient in req.to:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = req.subject
            msg["To"] = recipient
            msg["From"] = f'"{from_name}" <{from_email}>' if from_name else from_email
            msg.attach(MIMEText(req.html, "html"))

            if secure:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, context=context) as server:
                    server.login(user, password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(host, port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(user, password)
                    server.send_message(msg)

            results.append({"recipient": recipient, "status": "sent"})
        except Exception as e:
            results.append({"recipient": recipient, "status": "failed", "error": str(e)})

    sent = sum(1 for r in results if r["status"] == "sent")
    if sent == 0 and results:
        raise HTTPException(status_code=500, detail=results[0].get("error", "Send failed"))

    return {"success": True, "sent": sent, "results": results}
