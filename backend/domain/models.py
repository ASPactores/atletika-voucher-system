from pydantic import BaseModel, validator
from datetime import datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    access_token: str


class LoginResponse(BaseModel):
    id_token: str
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


class VoucherDetails(BaseModel):
    first_name: str
    last_name: str
    expiry_date: str
    percentage: str

    @validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, value):
        """Ensure expiry_date is a valid ISO 8601 datetime string."""
        try:
            datetime.fromisoformat(value)  # Validates ISO format
            return value
        except ValueError:
            raise ValueError(
                "expiry_date must be an ISO 8601 formatted string (e.g., '2024-12-31T23:59:59')"
            )


class ClaimVoucherRequest(BaseModel):
    voucher_id: str


class GenericResponse(BaseModel):
    message: str


class VoucherResponse(BaseModel):
    voucher_id: str
    first_name: str
    last_name: str
    expiry_date: str
    percentage: str
    status: str


class VoucherList(BaseModel):
    vouchers: list[VoucherResponse]
