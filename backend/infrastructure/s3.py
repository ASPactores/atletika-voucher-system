import boto3
import botocore
from core.config import config

s3 = boto3.client(
    "s3",
    region_name=config.AWS_REGION,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
)


def retrieve_template(template_name: str = "voucher-atletika.jpg") -> bytes:
    """
    Retrieves an object (template) from an S3 bucket.

    Args:
        template_name (str): The name of the template file.

    Returns:
        bytes: The binary content of the file.

    Raises:
        Exception: If the file is not found or there's an S3 error.
    """
    directory = f"templates/{template_name}"

    try:
        response = s3.get_object(Bucket=config.S3_BUCKET, Key=directory)
        return response["Body"].read()

    except s3.exceptions.NoSuchKey:
        raise FileNotFoundError(f"Template '{template_name}' not found in S3 bucket.")

    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        raise Exception(
            f"S3 ClientError: {error_code} - {e.response['Error']['Message']}"
        )

    except Exception as e:
        raise Exception(f"Unexpected error retrieving file from S3: {str(e)}")
