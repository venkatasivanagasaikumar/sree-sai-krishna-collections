import os
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load local environment variables from backend/.env if present (strictly gitignored)
_backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_file = os.path.join(_backend_root, ".env")
if os.path.exists(_env_file):
    load_dotenv(_env_file)
else:
    load_dotenv()

def _clean_str(val: str) -> str:
    """Strips leading/trailing whitespace and surrounding quotation marks."""
    if not val:
        return ""
    s = str(val).strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    return s

INSECURE_SECRET_PATTERNS = [
    "ssk-royal-navy-gold",
    "generate_with_openssl_rand_hex_32",
    "replace_with",
    "secret",
    "changeme",
    "password",
    "12345",
    "your_secret",
]

def is_secret_key_secure(secret: str) -> tuple[bool, str]:
    """
    Validates that a SECRET_KEY meets production security requirements:
    - Non-empty and not whitespace-only
    - Minimum length of 32 characters
    - Does not contain known development/default/placeholder patterns
    - Has adequate character diversity (entropy)
    Returns (is_secure, reason). Never includes the secret value in logs or reasons.
    """
    if not secret or not str(secret).strip():
        return False, "SECRET_KEY is empty or missing."
    s = str(secret).strip()
    if len(s) < 32:
        return False, f"SECRET_KEY length ({len(s)}) is below the required 32-character minimum."
    s_lower = s.lower()
    for pattern in INSECURE_SECRET_PATTERNS:
        if pattern in s_lower:
            return False, f"SECRET_KEY contains known insecure or default pattern '{pattern}'."
    if len(set(s)) < 8:
        return False, "SECRET_KEY has insufficient character entropy/diversity."
    return True, ""


def verify_production_secret_key(secret: str, environment: str = "production"):
    """
    Enforces that the SECRET_KEY is valid and secure when running in production.
    Raises RuntimeError if insecure in production. Passes silently in non-production.
    Never exposes the secret in the exception message.
    """
    if environment == "production":
        is_secure, sec_err = is_secret_key_secure(secret)
        if not is_secure:
            raise RuntimeError(f"CRITICAL MISCONFIGURATION: Insecure SECRET_KEY in production. {sec_err}")

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
    # Reads from MONGO_URI (recommended production key) or MONGODB_URI (backward compatibility)
    MONGO_URI: str = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_URI: str = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "ssk_production_db")
    FORCE_MOCK_DB: bool = os.getenv("FORCE_MOCK_DB", "true").lower() == "true"
    DB_MAX_POOL_SIZE: int = int(os.getenv("DB_MAX_POOL_SIZE", "50"))
    DB_MIN_POOL_SIZE: int = int(os.getenv("DB_MIN_POOL_SIZE", "10"))
    DB_MAX_IDLE_TIME_MS: int = int(os.getenv("DB_MAX_IDLE_TIME_MS", "45000"))
    DB_SERVER_SELECTION_TIMEOUT_MS: int = int(os.getenv("DB_SERVER_SELECTION_TIMEOUT_MS", "5000"))
    DB_CONNECT_TIMEOUT_MS: int = int(os.getenv("DB_CONNECT_TIMEOUT_MS", "10000"))
    DB_SOCKET_TIMEOUT_MS: int = int(os.getenv("DB_SOCKET_TIMEOUT_MS", "20000"))
    DB_TLS: bool = os.getenv("DB_TLS", "false").lower() == "true"

    @property
    def active_mongo_uri(self) -> str:
        """Returns the active MongoDB connection URI, prioritizing MONGO_URI while preserving test overrides."""
        if self.MONGODB_URI != self.MONGO_URI:
            if self.MONGODB_URI != "mongodb://localhost:27017" and self.MONGO_URI == "mongodb://localhost:27017":
                return self.MONGODB_URI
            if self.MONGO_URI != "mongodb://localhost:27017" and self.MONGODB_URI == "mongodb://localhost:27017":
                return self.MONGO_URI
            return self.MONGO_URI
        return self.MONGO_URI or self.MONGODB_URI
    
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

    # Cloudinary Product Image Storage
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    CLOUDINARY_FOLDER: str = os.getenv("CLOUDINARY_FOLDER", "products")

    @property
    def clean_cloudinary_cloud_name(self) -> str:
        return _clean_str(self.CLOUDINARY_CLOUD_NAME)

    @property
    def clean_cloudinary_api_key(self) -> str:
        return _clean_str(self.CLOUDINARY_API_KEY)

    @property
    def clean_cloudinary_api_secret(self) -> str:
        return _clean_str(self.CLOUDINARY_API_SECRET)

    @property
    def clean_cloudinary_folder(self) -> str:
        return _clean_str(self.CLOUDINARY_FOLDER) or "products"

    @property
    def is_cloudinary_configured(self) -> bool:
        """Returns True if all three required Cloudinary credentials are provided, non-empty, and not dummy masks."""
        c = self.clean_cloudinary_cloud_name
        k = self.clean_cloudinary_api_key
        s = self.clean_cloudinary_api_secret
        if not (c and k and s):
            return False
        # Guard against dashboard UI mask (e.g. '**********') or placeholder strings
        if set(s) == {"*"} or "your" in s.lower() or "placeholder" in s.lower():
            return False
        return True

    def validate_production_readiness(self) -> List[str]:
        """
        Validates critical configuration against production security benchmarks.
        Returns a list of warning or blocker strings.
        """
        blockers = []
        if self.ENVIRONMENT == "production":
            is_valid_sec, sec_reason = is_secret_key_secure(self.SECRET_KEY)
            if not is_valid_sec:
                blockers.append(f"SECRET_KEY is insecure for production: {sec_reason}")
            if self.FORCE_MOCK_DB:
                blockers.append("FORCE_MOCK_DB is True in production environment.")
            active_uri = self.active_mongo_uri
            if "localhost" in active_uri or "127.0.0.1" in active_uri:
                blockers.append("MONGO_URI / MONGODB_URI points to localhost in production mode.")
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
            if any([self.CLOUDINARY_CLOUD_NAME, self.CLOUDINARY_API_KEY, self.CLOUDINARY_API_SECRET]):
                if not (self.clean_cloudinary_cloud_name and self.clean_cloudinary_api_key and self.clean_cloudinary_api_secret):
                    blockers.append("Cloudinary configuration is incomplete: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET must all be provided.")
                elif set(self.clean_cloudinary_api_secret) == {"*"}:
                    blockers.append("CLOUDINARY_API_SECRET is set to masked asterisks (e.g. '**********') instead of the actual secret.")
            elif not self.is_cloudinary_configured:
                blockers.append("Cloudinary product image storage is required in production (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET must be configured).")
        return blockers
    
settings = Settings()
