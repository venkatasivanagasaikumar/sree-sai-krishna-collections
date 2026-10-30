from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import logger
from app.database import db_manager, get_db
from app.seeds.seed_data import run_seed

# Import routers
import os
from fastapi.staticfiles import StaticFiles
from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.categories import router as categories_router
from app.api.v1.cart import router as cart_router
from app.api.v1.orders import router as orders_router
from app.api.v1.payments import router as payments_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.returns import router as returns_router
from app.api.v1.coupons import router as coupons_router
from app.api.v1.customers import router as customers_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.settings import router as settings_router
from app.api.v1.upload import router as upload_router
from app.api.v1.sheets_sync import router as sheets_router
from app.api.v1.shipping import router as shipping_router
from app.api.v1.invoices import router as invoices_router
from app.api.v1.communications import router as communications_router
from app.api.v1.webhooks import router as webhooks_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} (Environment: {settings.ENVIRONMENT})...")
    
    # Production security & readiness check
    blockers = settings.validate_production_readiness()
    if blockers:
        for b in blockers:
            logger.warning(f"[PRODUCTION CONFIG ALERT] {b}")

    db = get_db()
    try:
        if db.users.count_documents({}) == 0 or db.categories.count_documents({}) == 0:
            logger.info("Empty database detected. Executing initial system seeds...")
            run_seed()
    except Exception as e:
        logger.warning(f"Seed initialization check note: {e}")
    yield
    # Graceful shutdown
    db_manager.persist_to_disk()
    db_manager.close()
    logger.info(f"Graceful shutdown of {settings.PROJECT_NAME} complete.")

is_prod = settings.ENVIRONMENT == "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack enterprise API for Sree Sai Krishna Collections (SSK) jewellery & accessories.",
    version="1.0.0",
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json",
    lifespan=lifespan
)

# CORS Middleware with dynamic origins support
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(categories_router, prefix=settings.API_V1_STR)
app.include_router(cart_router, prefix=settings.API_V1_STR)
app.include_router(orders_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)
app.include_router(inventory_router, prefix=settings.API_V1_STR)
app.include_router(returns_router, prefix=settings.API_V1_STR)
app.include_router(coupons_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(upload_router, prefix=settings.API_V1_STR)
app.include_router(sheets_router, prefix=settings.API_V1_STR)
app.include_router(shipping_router, prefix=settings.API_V1_STR)
app.include_router(invoices_router, prefix=settings.API_V1_STR)
app.include_router(communications_router, prefix=settings.API_V1_STR)
app.include_router(webhooks_router, prefix=settings.API_V1_STR)

# Mount /uploads directory for static image serving
UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/health")
def health_check():
    """Liveness probe: verifies process is alive and responsive."""
    return {
        "status": "healthy",
        "brand": settings.BRAND_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "mock_file_backed" if db_manager.is_mock else "mongodb_live"
    }

@app.get("/ready")
def readiness_check():
    """Readiness probe: validates database connectivity and readiness for customer traffic."""
    try:
        ping_res = db_manager.ping()
        db = get_db()
        return {
            "status": "ready",
            "environment": settings.ENVIRONMENT,
            "database": ping_res,
            "products_count": db.products.count_documents({}),
            "orders_count": db.orders.count_documents({})
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": "Database unavailable", "detail": str(e)}
        )

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.BRAND_NAME} (SSK) API",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready"
    }
