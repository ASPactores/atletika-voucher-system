from fastapi import FastAPI
from mangum import Mangum
from api import auth, vouchers
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(vouchers.router, prefix="/vouchers", tags=["Vouchers"])

handler = Mangum(app)
