from fastapi import APIRouter, HTTPException, Response
from domain.models import LoginRequest, LoginResponse, GenericResponse, LogoutRequest
from services.auth_service import login, logout
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login_user(request: LoginRequest, response: Response):
    try:
        cookies = login(request)
        response.set_cookie(
            key="access_token",
            value=cookies.access_token,
            max_age=cookies.expires_in,
            samesite="Lax",
        )
        response.set_cookie(
            key="refresh_token",
            value=cookies.refresh_token,
            max_age=604800,  # 7 days
            samesite="Lax",
        )
        response.set_cookie(
            key="id_token",
            value=cookies.id_token,
            max_age=cookies.expires_in,
            samesite="Lax",
        )

        # return JSONResponse(content=cookies, status_code=200)
        return cookies

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout", response_model=GenericResponse)
async def logout_user(
    request: LogoutRequest,
    response: Response,
):
    try:
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        response.delete_cookie(key="id_token")
        return logout(request=request)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
