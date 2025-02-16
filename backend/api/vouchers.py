from fastapi import APIRouter, Depends, HTTPException
from services.voucher_service import (
    create_voucher,
    claim_voucher,
    get_all_vouchers,
    get_voucher,
)
from domain.models import (
    VoucherDetails,
    ClaimVoucherRequest,
    GenericResponse,
    VoucherList,
    VoucherResponse,
)
from infrastructure.cognito import verify_token
from botocore.exceptions import ClientError, BotoCoreError
from fastapi.responses import StreamingResponse


router = APIRouter()


@router.post("/generate", response_model=VoucherDetails)
async def generate_voucher(
    voucher_details: VoucherDetails, token: str = Depends(verify_token)
):
    try:
        voucher = create_voucher(
            voucher_details.first_name,
            voucher_details.last_name,
            voucher_details.expiry_date,
            voucher_details.percentage,
        )
        return StreamingResponse(
            content=voucher,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=Atletika_Voucher.pdf"
            },
        )

    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"DynamoDB error: {ce.response['Error']['Message']}"
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except BotoCoreError as be:
        raise HTTPException(status_code=503, detail=f"AWS service error: {str(be)}")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/claim", response_model=GenericResponse)
async def claim_voucher_endpoint(
    claim_request: ClaimVoucherRequest, token: str = Depends(verify_token)
):
    try:
        claim_voucher(claim_request.voucher_id)
        return GenericResponse(message="Voucher successfully claimed.")

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
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


@router.get("/all", response_model=VoucherList)
async def get_vouchers(token: str = Depends(verify_token)):
    try:
        vouchers = get_all_vouchers()
        return VoucherList(
            vouchers=[
                {
                    "voucher_id": voucher["voucher-id"],
                    "first_name": voucher["first-name"],
                    "last_name": voucher["last-name"],
                    "percentage": voucher["percentage"],
                    "status": voucher["status"],
                }
                for voucher in vouchers
            ]
        )

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


@router.get("/{voucher_id}", response_model=VoucherResponse)
async def get_single_voucher(voucher_id: str, token: str = Depends(verify_token)):
    try:
        voucher = get_voucher(voucher_id)
        return voucher
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except ClientError as ce:
        raise HTTPException(
            status_code=500, detail=f"DynamoDB error: {ce.response['Error']['Message']}"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
