from dataclasses import dataclass
from constants.enums import VoucherStatus


@dataclass
class Voucher:
    voucher_id: str
    first_name: str
    last_name: str
    percentage: str
    status: str = VoucherStatus.UNUSED.value

    def mark_as_used(self):
        if self.status == VoucherStatus.USED.value:
            raise ValueError("Voucher has already been used.")
        self.status = VoucherStatus.USED.value
