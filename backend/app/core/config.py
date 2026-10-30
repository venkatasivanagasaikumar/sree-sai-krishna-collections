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
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ALLOW_MOCK_PAYMENTS: bool = os.getenv("ALLOW_MOCK_PAYMENTS", "true").lower() == "true"

    # MongoDB Config (Supports Atlas mongodb+srv:// and standard replica sets)
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "ssk_collections_db")
    FORCE_MOCK_DB: bool = os.getenv("FORCE_MOCK_DB", "true").lower() == "true"
    DB_MAX_POOL_SIZE: int = int(os.getenv("DB_MAX_POOL_SIZE", "50"))
    DB_MIN_POOL_SIZE: int = int(os.getenv("DB_MIN_POOL_SIZE", "10"))
    DB_MAX_IDLE_TIME_MS: int = int(os.getenv("DB_MAX_IDLE_TIME_MS", "45000"))
    DB_SERVER_SELECTION_TIMEOUT_MS: int = int(os.getenv("DB_SERVER_SELECTION_TIMEOUT_MS", "5000"))
    DB_CONNECT_TIMEOUT_MS: int = int(os.getenv("DB_CONNECT_TIMEOUT_MS", "10000"))
    DB_SOCKET_TIMEOUT_MS: int = int(os.getenv("DB_SOCKET_TIMEOUT_MS", "20000"))
    DB_TLS: bool = os.getenv("DB_TLS", "false").lower() == "true"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://sreesaikrishnacollections.com",
        "https://www.sreesaikrishnacollections.com",
        "https://admin.sreesaikrishnacollections.com"
    ]

    @property
    def cors_origins(self) -> List[str]:
        raw = os.getenv("BACKEND_CORS_ORIGINS")
        if raw:
            try:
                import json
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [orig.strip() for orig in raw.split(",") if orig.strip()]
        return self.BACKEND_CORS_ORIGINS
    
    # Payments (Razorpay Sandbox/Config)
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_SSKJewelleryDemo2026")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "SSKTestSecretMockSignatureKey")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "SSKWebhookSecret2026")
    ENABLE_COD: bool = True
    COD_MIN_ORDER_AMOUNT: float = 299.0
    COD_MAX_ORDER_AMOUNT: float = 50000.0
    FREE_SHIPPING_THRESHOLD: float = 999.0
    STANDARD_SHIPPING_FEE: float = 79.0
    
    # Business details
    SUPPORT_EMAIL: str = "support@sreesaikrishnacollections.com"
    SUPPORT_PHONE: str = "+91 98480 22338"
    BUSINESS_ADDRESS: str = "Shop #12, Sri Krishna Temple Street, Near Clock Tower, Secunderabad, Telangana - 500003, India"
    
    # SMTP / Transactional Email Config
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "orders@sreesaikrishnacollections.com")
    SMTP_FROM_NAME: str = "Sree Sai Krishna Collections"
    EMAILS_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "orders@sreesaikrishnacollections.com")
    EMAILS_FROM_NAME: str = "Sree Sai Krishna Collections"
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # GST & Invoicing Configuration
    SELLER_GSTIN: str = os.getenv("SELLER_GSTIN", "") # Configurable pending accountant verification
    SELLER_STATE: str = "Telangana"
    SELLER_STATE_CODE: str = "36"
    SELLER_PAN: str = os.getenv("SELLER_PAN", "AAECS1234F")
    DEFAULT_JEWELLERY_GST_RATE: float = 0.03 # 3% for gold & imitation jewellery (HSN 7113/7117)
    DEFAULT_ACCESSORIES_GST_RATE: float = 0.18 # 18% for hair clips, claws, bands (HSN 9615)
    INVOICE_PREFIX: str = "SSK-INV"
    CREDIT_NOTE_PREFIX: str = "SSK-CN"
    
    # WhatsApp Meta Cloud API Configuration
    WHATSAPP_ENABLED: bool = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_API_VERSION: str = os.getenv("WHATSAPP_API_VERSION", "v19.0")
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ssk_wa_verify_token_2026")
    WHATSAPP_APP_SECRET: str = os.getenv("WHATSAPP_APP_SECRET", "")

    # Initial Admin Initialization & Security
    INITIAL_ADMIN_EMAIL: str = os.getenv("INITIAL_ADMIN_EMAIL", "admin@sskcollections.com")
    INITIAL_ADMIN_PASSWORD: str = os.getenv("INITIAL_ADMIN_PASSWORD", "")

    def validate_production_readiness(self) -> List[str]:
        """
        Validates critical configuration against production security benchmarks.
        Returns a list of warning or blocker strings.
        """
        blockers = []
        if self.ENVIRONMENT == "production":
            if "ssk-royal-navy-gold" in self.SECRET_KEY or self.SECRET_KEY == "generate_with_openssl_rand_hex_32":
                blockers.append("SECRET_KEY is using insecure default development value.")
            if self.FORCE_MOCK_DB:
                blockers.append("FORCE_MOCK_DB is True in production environment.")
            if "localhost" in self.MONGODB_URI or "127.0.0.1" in self.MONGODB_URI:
                blockers.append("MONGODB_URI points to localhost in production mode.")
            if self.RAZORPAY_KEY_ID.startswith("rzp_live_"):
                if not self.RAZORPAY_KEY_SECRET or self.RAZORPAY_KEY_SECRET == "YOUR_RAZORPAY_KEY_SECRET":
                    blockers.append("RAZORPAY_KEY_SECRET is unconfigured for live Razorpay key.")
                if not self.RAZORPAY_WEBHOOK_SECRET or self.RAZORPAY_WEBHOOK_SECRET == "YOUR_RAZORPAY_WEBHOOK_SECRET":
                    blockers.append("RAZORPAY_WEBHOOK_SECRET is unconfigured for live Razorpay key.")
            if self.WHATSAPP_ENABLED and not self.WHATSAPP_ACCESS_TOKEN:
                blockers.append("WHATSAPP_ENABLED is True but WHATSAPP_ACCESS_TOKEN is missing.")
            if self.SMTP_HOST and not self.SMTP_USER:
                blockers.append("SMTP_HOST configured but SMTP_USER is missing.")
            if not self.INITIAL_ADMIN_PASSWORD or self.INITIAL_ADMIN_PASSWORD in ["Admin@SSK2026!", "Staff@SSK2026!", "AdminPassword123!"]:
                blockers.append("INITIAL_ADMIN_PASSWORD must be configured with a secure non-default password in production.")
        return blockers
    
settings = Settings()
