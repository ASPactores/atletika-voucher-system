from fastapi import HTTPException
import io
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from dotenv import load_dotenv

load_dotenv()


def send_email(
    email: str, pdf_data: io.BytesIO, filename: str = "Atletika_Voucher.pdf"
):
    msg = MIMEMultipart()
    msg["From"] = os.getenv("EMAIL_ADDRESS")
    msg["To"] = email
    msg["Subject"] = "🎉 Congratulations! You've Received an Atletika Voucher!"

    body = """
    <html>
    <body>
        <p>Hello,</p>
        <p>We hope you're doing great! You have received an exclusive discount voucher from Atletika.</p>
        <p><strong>Your voucher is attached to this email.</strong></p>
        <p>Simply present it to any Atletika team member and enjoy your special discount on Atletika merchandise.</p>
        <p>Thank you for being a part of the Atletika family. Happy shopping!</p>
        <p><strong>- The Atletika Team<strong></p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, "html"))

    pdf_data.seek(0)
    attachment = MIMEApplication(pdf_data.read(), _subtype="pdf")
    attachment.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(attachment)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_APP_PASSWORD"))
            server.sendmail(msg["From"], msg["To"], msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")
