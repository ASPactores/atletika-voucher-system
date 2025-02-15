from pydantic import BaseModel


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
    percentage: str


class ClaimVoucherRequest(BaseModel):
    voucher_id: str


class GenericResponse(BaseModel):
    message: str


class VoucherResponse(BaseModel):
    voucher_id: str
    first_name: str
    last_name: str
    percentage: str
    status: str


class VoucherList(BaseModel):
    vouchers: list[VoucherResponse]
