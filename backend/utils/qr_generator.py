import io
import qrcode
from PIL import Image
from fastapi import HTTPException
from datetime import datetime
from infrastructure.s3 import retrieve_template
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_qr_code(unique_id: str, expiry_date: str) -> io.BytesIO:
    try:
        # Fetch the image from S3 as bytes
        img_bytes = retrieve_template("voucher-atletika.png")
        base_image = Image.open(io.BytesIO(img_bytes))

        # Ensure PNG is in RGB mode
        if base_image.mode in ("RGBA", "LA"):
            white_bg = Image.new("RGB", base_image.size, (255, 255, 255))
            white_bg.paste(
                base_image, mask=base_image.split()[3]
            )  # Apply alpha channel as mask
            base_image = white_bg

        img_width, img_height = base_image.size

        image_io = io.BytesIO()
        base_image.save(image_io, format="PNG", optimize=True)
        image_io.seek(0)
        image_reader = ImageReader(image_io)

        pdf_io = io.BytesIO()
        pdf_canvas = canvas.Canvas(pdf_io, pagesize=(img_width, img_height))

        pdf_canvas.drawImage(image_reader, 0, 0, width=img_width, height=img_height)

        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(unique_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")

        qr_size = 515
        qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

        # Convert QR code to ImageReader
        qr_io = io.BytesIO()
        qr_img.save(qr_io, format="PNG")
        qr_io.seek(0)
        qr_reader = ImageReader(qr_io)

        # Position QR Code
        qr_x = 22
        qr_y = 43
        pdf_canvas.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)

        expiry_dt = datetime.fromisoformat(expiry_date)
        formatted_date = expiry_dt.strftime("%B %d, %Y")

        pdf_canvas.setFont("Helvetica-Bold", 20)
        text_x = 960
        text_y = 80
        pdf_canvas.drawString(text_x, text_y, formatted_date)

        pdf_canvas.showPage()
        pdf_canvas.save()

        pdf_io.seek(0)
        return pdf_io

    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))

    except IOError as ie:
        raise HTTPException(
            status_code=500, detail=f"Image processing error: {str(ie)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"QR code PDF generation failed: {str(e)}"
        )
