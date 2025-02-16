import uuid
from io import BytesIO
from domain.models import VoucherResponse
from domain.entities import Voucher
from infrastructure.dynamodb import table
from utils.qr_generator import generate_qr_code
from utils.send_email import send_email
from constants.enums import VoucherStatus


# TODO: Remove this import
import os
from dotenv import load_dotenv

load_dotenv()


def create_voucher(
    first_name: str,
    last_name: str,
    expiry_date: str,
    percentage: str,
) -> BytesIO:
    unique_id = str(uuid.uuid4())
    image = generate_qr_code(unique_id, expiry_date)

    # TODO: Remove this line. This is just for testing purposes.
    send_email(os.getenv("EMAIL_ADDRESS"), image)

    voucher = {
        "voucher-id": unique_id,
        "first-name": first_name,
        "last-name": last_name,
        "expiry-date": expiry_date,
        "percentage": percentage,
        "status": VoucherStatus.UNUSED.value,
    }

    table.put_item(Item=voucher)
    return image


def claim_voucher(voucher_id: str):
    response = table.get_item(Key={"voucher-id": voucher_id})
    voucher_data = response.get("Item")

    if not voucher_data:
        raise ValueError("Voucher not found.")

    voucher = Voucher(
        voucher_id=voucher_data["voucher-id"],
        first_name=voucher_data["first-name"],
        last_name=voucher_data["last-name"],
        expiry_date=voucher_data["expiry-date"],
        percentage=voucher_data["percentage"],
        status=voucher_data["status"],
    )
    voucher.mark_as_used()

    table.update_item(
        Key={"voucher-id": voucher_id},
        UpdateExpression="SET #status = :new_status",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":new_status": VoucherStatus.USED.value},
    )

    return voucher


def get_voucher(voucher_id: str) -> Voucher:
    response = table.get_item(Key={"voucher-id": voucher_id})
    voucher_data = response.get("Item")

    if not voucher_data:
        raise ValueError("Voucher not found.")

    voucher = VoucherResponse(
        voucher_id=voucher_data["voucher-id"],
        first_name=voucher_data["first-name"],
        last_name=voucher_data["last-name"],
        expiry_date=voucher_data["expiry-date"],
        percentage=voucher_data["percentage"],
        status=voucher_data["status"],
    )

    return voucher


def get_all_vouchers():
    try:
        response = table.scan()
        vouchers = response.get("Items", [])

        return vouchers

    except Exception as e:
        raise e
