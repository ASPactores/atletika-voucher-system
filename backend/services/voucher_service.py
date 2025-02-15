import uuid
from domain.models import VoucherList
from domain.entities import Voucher
from infrastructure.dynamodb import table
from utils.qr_generator import generate_qr_code
from constants.enums import VoucherStatus


def create_voucher(first_name: str, last_name: str, percentage: str) -> Voucher:
    unique_id = str(uuid.uuid4())
    image = generate_qr_code(unique_id)

    voucher = {
        "voucher-id": unique_id,
        "first-name": first_name,
        "last-name": last_name,
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


def get_all_vouchers():
    try:
        response = table.scan()
        vouchers = response.get("Items", [])

        return vouchers

    except Exception as e:
        raise e
