import io
import logging
import os
import uuid
import qrcode
import boto3
from dotenv import load_dotenv
from mangum import Mangum
from PIL import Image
import requests
import jwt
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError
from fastapi import FastAPI, HTTPException, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import base64
import hashlib
import hmac

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

app = FastAPI()
handler = Mangum(app)

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_KEYS_URL = os.getenv("COGNITO_KEYS_URL")

# Initialize Cognito client
client = boto3.client("cognito-idp", region_name=AWS_REGION)


def get_cognito_public_keys():
    response = requests.get(COGNITO_KEYS_URL)
    response.raise_for_status()
    return {key["kid"]: key for key in response.json()["keys"]}


COGNITO_KEYS = get_cognito_public_keys()
security = HTTPBearer()


def verify_token(auth: HTTPAuthorizationCredentials = Security(security)):
    token = auth.credentials

    try:
        # Decode JWT header
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        if kid not in COGNITO_KEYS:
            raise HTTPException(status_code=401, detail="Invalid token header.")

        # Get public key
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(COGNITO_KEYS[kid])

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}",
        )

        # Validate the client_id manually
        if payload.get("client_id") != COGNITO_CLIENT_ID:
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


# Request models
class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    access_token: str


# Response model
class LoginResponse(BaseModel):
    id_token: str
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


def calculate_secret_hash(username: str) -> str:
    """Generate Cognito secret hash"""
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with AWS Cognito and return JWT tokens.
    """

    try:
        secret_hash = calculate_secret_hash(request.email)

        response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": request.email,
                "PASSWORD": request.password,
                "SECRET_HASH": secret_hash,
            },
        )

        return {
            "id_token": response["AuthenticationResult"]["IdToken"],
            "access_token": response["AuthenticationResult"]["AccessToken"],
            "refresh_token": response["AuthenticationResult"]["RefreshToken"],
            "expires_in": response["AuthenticationResult"]["ExpiresIn"],
            "token_type": response["AuthenticationResult"]["TokenType"],
        }

    except client.exceptions.NotAuthorizedException as nae:
        print("NotAuthorizedException: ", nae)
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    except client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found.")

    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"Cognito error: {ce.response['Error']['Message']}"
        )

    except BotoCoreError as be:
        raise HTTPException(status_code=503, detail=f"AWS service error: {str(be)}")

    except HTTPException as he:
        raise he

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.post("/logout")
async def logout(request: LogoutRequest):
    """
    Invalidate user token by revoking AWS Cognito access token.
    """
    try:
        client.global_sign_out(AccessToken=request.access_token)
        return {"message": "User logged out successfully."}

    except client.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"Cognito error: {ce.response['Error']['Message']}"
        )

    except BotoCoreError as be:
        raise HTTPException(status_code=503, detail=f"AWS service error: {str(be)}")

    except HTTPException as he:
        raise he

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")


if not all([AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DYNAMODB_TABLE]):
    raise ValueError("Missing AWS configuration in environment variables.")

# Initialize DynamoDB
dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

table = dynamodb.Table(DYNAMODB_TABLE)


class VoucherDetails(BaseModel):
    first_name: str
    last_name: str
    percentage: str


@app.get("/")
async def read_root():
    return {"Hello": "World"}


def generate_qr_code(unique_id: str):
    try:
        file = "voucher-atletika.jpg"

        # Ensure the file exists
        if not os.path.exists(file):
            raise FileNotFoundError(f"Background image '{file}' not found.")

        image = Image.open(file)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(unique_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")

        # Resize QR code to fit the white space (assuming a predefined size)
        qr_size = (500, 500)
        qr_img = qr_img.resize(qr_size, Image.Resampling.LANCZOS)

        # Paste QR code onto the image at the predefined white space location
        image.paste(qr_img, (29, 43))

        # Save to a BytesIO stream
        img_io = io.BytesIO()
        image.save(img_io, format="JPEG")
        img_io.seek(0)

        return img_io

    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))

    except IOError as ie:
        raise HTTPException(
            status_code=500, detail=f"Image processing error: {str(ie)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"QR code generation failed: {str(e)}"
        )


async def save_to_dynamo_db(item: VoucherDetails, unique_id: str):
    try:
        data = {
            "voucher-id": unique_id,
            "first-name": item.first_name,
            "last-name": item.last_name,
            "percentage": item.percentage,
            "status": "unused",
        }

        table.put_item(Item=data)

    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found.")

    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"DynamoDB error: {ce.response['Error']['Message']}"
        )

    except BotoCoreError as be:
        raise HTTPException(status_code=503, detail=f"AWS service error: {str(be)}")

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database save failed: {str(e)}")


@app.post("/generate-qr-code", response_class=StreamingResponse)
async def add_entry(
    item: VoucherDetails, user: dict = Depends(verify_token)
) -> StreamingResponse:
    try:
        unique_id = str(uuid.uuid4())
        image = generate_qr_code(unique_id)
        await save_to_dynamo_db(item, unique_id)

        logger.info(f"User {user['username']} generated a voucher with ID {unique_id}.")

        return StreamingResponse(image, media_type="image/jpeg")

    except HTTPException as he:
        raise he

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class ClaimVoucherRequest(BaseModel):
    voucher_id: str


class GenericResponse(BaseModel):
    message: str


@app.post("/claim-voucher", response_model=GenericResponse)
async def claim_voucher(
    request: ClaimVoucherRequest, user: dict = Depends(verify_token)
):
    try:
        response = table.get_item(Key={"voucher-id": request.voucher_id})
        voucher = response.get("Item")

        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found.")

        if voucher["status"] == "used":
            raise HTTPException(
                status_code=400, detail="Voucher has already been used."
            )

        table.update_item(
            Key={"voucher-id": request.voucher_id},
            UpdateExpression="SET #status = :new_status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":new_status": "used"},
        )

        logger.info(
            f"User {user['username']} claimed a voucher with ID {request.voucher_id}."
        )

        return GenericResponse(message="Voucher successfully claimed.")

    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"DynamoDB error: {ce.response['Error']['Message']}"
        )
    except BotoCoreError as be:
        raise HTTPException(status_code=503, detail=f"AWS service error: {str(be)}")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class VoucherResponse(BaseModel):
    voucher_i: str
    first_name: str
    last_name: str
    percentage: str
    status: str


class VoucherList(BaseModel):
    vouchers: list[VoucherResponse]


@app.get("/vouchers", response_model=VoucherList)
async def get_all_vouchers(user: dict = Depends(verify_token)):
    try:
        response = table.scan()
        vouchers = response.get("Items", [])

        return VoucherList(vouchers=vouchers)

    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"DynamoDB error: {ce.response['Error']['Message']}"
        )
    except BotoCoreError as be:
        raise HTTPException(status_code=503, detail=f"AWS service error: {str(be)}")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
