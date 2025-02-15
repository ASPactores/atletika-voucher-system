import requests
import jwt
import hmac
import hashlib
import base64
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import config
import boto3

security = HTTPBearer()
client = boto3.client("cognito-idp", region_name=config.AWS_REGION)


def get_cognito_public_keys():
    response = requests.get(config.COGNITO_KEYS_URL)
    response.raise_for_status()
    return {key["kid"]: key for key in response.json()["keys"]}


COGNITO_KEYS = get_cognito_public_keys()


def verify_token(auth: HTTPAuthorizationCredentials = Security(security)):
    token = auth.credentials
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        if kid not in COGNITO_KEYS:
            raise HTTPException(status_code=401, detail="Invalid token header.")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(COGNITO_KEYS[kid])

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=f"https://cognito-idp.{config.AWS_REGION}.amazonaws.com/{config.COGNITO_USER_POOL_ID}",
        )

        if payload.get("client_id") != config.COGNITO_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Invalid client_id in token.")

        if "admin" not in payload.get("cognito:groups", []):
            raise HTTPException(
                status_code=401,
                detail="You are not authorized to access this resource.",
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
