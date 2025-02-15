import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
    COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
    COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
    COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
    COGNITO_KEYS_URL = os.getenv("COGNITO_KEYS_URL")


config = Config()
