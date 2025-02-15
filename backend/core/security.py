import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service import calculate_secret_hash
from core.config import config
import requests

security = HTTPBearer()


def get_cognito_public_keys():
    response = requests.get(config.COGNITO_KEYS_URL)
    response.raise_for_status()
    return {key["kid"]: key for key in response.json()["keys"]}


def verify_token(auth: HTTPAuthorizationCredentials = Security(security)):
    cognito_keys = get_cognito_public_keys()
    token = auth.credentials

    try:
        # Decode JWT header
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        if kid not in cognito_keys:
            raise HTTPException(status_code=401, detail="Invalid token header.")

        # Get public key
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(cognito_keys[kid])

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=f"https://cognito-idp.{config.AWS_REGION}.amazonaws.com/{config.COGNITO_USER_POOL_ID}",
        )

        # Validate the client_id manually
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
