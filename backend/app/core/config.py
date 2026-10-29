import os
from typing import List
from pydantic import BaseModel, Field

class Settings(BaseModel):
    PROJECT_NAME: str = "Sree Sai Krishna Collections API"
    BRAND_NAME: str = "Sree Sai Krishna Collections"
    BRAND_SHORT_NAME: str = "SSK"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "ssk-royal-navy-gold-super-secure-jwt-secret-key-2026-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # MongoDB Config
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "ssk_collections_db")
    FORCE_MOCK_DB: bool = os.getenv("FORCE_MOCK_DB", "true").lower() == "true"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Payments (Razorpay Sandbox/Config)
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_SSKJewelleryDemo2026")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "SSKTestSecretMockSignatureKey")
    ENABLE_COD: bool = True
    COD_MIN_ORDER_AMOUNT: float = 299.0
    COD_MAX_ORDER_AMOUNT: float = 50000.0
    FREE_SHIPPING_THRESHOLD: float = 999.0
    STANDARD_SHIPPING_FEE: float = 79.0
    
    # Business details
    SUPPORT_EMAIL: str = "support@sreesaikrishnacollections.com"
    SUPPORT_PHONE: str = "+91 98480 22338"
    BUSINESS_ADDRESS: str = "Shop #12, Sri Krishna Temple Street, Near Clock Tower, Secunderabad, Telangana - 500003, India"
    
settings = Settings()
