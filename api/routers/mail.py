from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

router = APIRouter()

@router.post("/mail",)
async def send_mail(
    subject: str = Form(...),
    name: str = Form(...),
    from_email: str = Form(...),
    text: str = Form(...),
):
   smtp_server = "158.217.174.41"
   port = 25
  
   message = MIMEMultipart()
   message["Subject"] = subject
   message["From"] = formataddr((name, from_email))
   message["To"] = "ebara@kansai-u.ac.jp"
   text = MIMEText(text)
   message.attach(text)
   try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.send_message(message)
        server.quit()
        return JSONResponse(content={"message": "Mail sent successfully"})
   except Exception as e:
        print({str(e)})
        return JSONResponse(content={"message": str(e)}, status_code=500)



