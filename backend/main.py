from fastapi import FastAPI
from mangum import Mangum
from api import auth, vouchers

app = FastAPI()

# Include routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(vouchers.router, prefix="/vouchers", tags=["Vouchers"])

handler = Mangum(app)
