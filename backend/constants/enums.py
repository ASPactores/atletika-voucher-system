from enum import Enum


class VoucherStatus(str, Enum):
    UNUSED = "unused"
    USED = "used"
