from infrastructure.cognito import client
from core.config import config
from domain.models import LoginRequest, LoginResponse, LogoutRequest, GenericResponse
import hmac
import hashlib
import base64
from fastapi import HTTPException
from botocore.exceptions import ClientError, BotoCoreError


def calculate_secret_hash(username: str) -> str:
    message = username + config.COGNITO_CLIENT_ID
    dig = hmac.new(
        config.COGNITO_CLIENT_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


def login(request: LoginRequest) -> LoginResponse:
    try:
        secret_hash = calculate_secret_hash(request.email)
        response = client.initiate_auth(
            ClientId=config.COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": request.email,
                "PASSWORD": request.password,
                "SECRET_HASH": secret_hash,
            },
        )
        return LoginResponse(
            access_token=response["AuthenticationResult"]["AccessToken"],
            refresh_token=response["AuthenticationResult"]["RefreshToken"],
            id_token=response["AuthenticationResult"]["IdToken"],
            token_type=response["AuthenticationResult"]["TokenType"],
            expires_in=response["AuthenticationResult"]["ExpiresIn"],
        )

    except client.exceptions.NotAuthorizedException as nae:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    except client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found.")

    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"Cognito error: {ce.response['Error']['Message']}"
        )

    except BotoCoreError as be:
        raise HTTPException(status_code=503, detail=f"AWS service error: {str(be)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def logout(request: LogoutRequest) -> GenericResponse:
    try:
        response = client.global_sign_out(AccessToken=request.access_token)
        return GenericResponse(message="User logged out successful.")

    except client.exceptions.NotAuthorizedException as nae:
        raise HTTPException(status_code=401, detail="Invalid access token.")

    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"Cognito error: {ce.response['Error']['Message']}"
        )

    except BotoCoreError as be:
        raise HTTPException(status_code=503, detail=f"AWS service error: {str(be)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
