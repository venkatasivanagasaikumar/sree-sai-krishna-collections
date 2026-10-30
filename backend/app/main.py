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

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME}...")
    db = get_db()
    try:
        if db.users.count_documents({}) == 0 or db.categories.count_documents({}) == 0:
            logger.info("Empty database detected. Executing initial system seeds...")
            run_seed()
    except Exception as e:
        logger.warning(f"Seed initialization check note: {e}")
    yield
    db_manager.persist_to_disk()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack enterprise API for Sree Sai Krishna Collections (SSK) jewellery & accessories.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
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

# Mount /uploads directory for static image serving
UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/health")
def health_check():
    db = get_db()
    return {
        "status": "healthy",
        "brand": settings.BRAND_NAME,
        "database": "mock_file_backed" if db_manager.is_mock else "mongodb_live",
        "products_count": db.products.count_documents({}),
        "orders_count": db.orders.count_documents({})
    }

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.BRAND_NAME} (SSK) API",
        "docs": "/docs",
        "health": "/health"
    }
