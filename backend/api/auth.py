from fastapi import APIRouter, Depends, HTTPException
from domain.models import LoginRequest, LoginResponse, GenericResponse, LogoutRequest
from services.auth_service import login, logout


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login_user(request: LoginRequest):
    try:
        return login(request)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout", response_model=GenericResponse)
async def logout_user(
    request: LogoutRequest,
):
    try:
        return logout(request=request)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
