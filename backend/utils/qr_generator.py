import io
import os
import qrcode
from PIL import Image
from fastapi import HTTPException


def generate_qr_code(unique_id: str):
    try:
        file = "voucher-atletika.jpg"

        # Ensure the file exists
        if not os.path.exists(file):
            raise FileNotFoundError(f"Background image '{file}' not found.")

        image = Image.open(file)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(unique_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")

        # Resize QR code to fit the white space (assuming a predefined size)
        qr_size = (500, 500)
        qr_img = qr_img.resize(qr_size, Image.Resampling.LANCZOS)

        # Paste QR code onto the image at the predefined white space location
        image.paste(qr_img, (29, 43))

        # Save to a BytesIO stream
        img_io = io.BytesIO()
        image.save(img_io, format="JPEG")
        img_io.seek(0)

        return img_io

    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))

    except IOError as ie:
        raise HTTPException(
            status_code=500, detail=f"Image processing error: {str(ie)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"QR code generation failed: {str(e)}"
        )
