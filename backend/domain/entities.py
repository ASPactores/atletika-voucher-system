from dataclasses import dataclass
from datetime import datetime
from constants.enums import VoucherStatus
from fastapi import HTTPException


@dataclass
class Voucher:
    voucher_id: str
    first_name: str
    last_name: str
    expiry_date: str
    percentage: str
    status: str = VoucherStatus.UNUSED.value

    def mark_as_used(self):
        if self.status == VoucherStatus.USED.value:
            raise HTTPException(
                status_code=400, detail="Voucher has already been claimed."
            )
        if datetime.now() > datetime.fromisoformat(self.expiry_date):
            raise HTTPException(status_code=400, detail="Voucher has expired.")
        self.status = VoucherStatus.USED.value
