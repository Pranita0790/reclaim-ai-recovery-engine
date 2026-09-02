from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import (
    BusinessValidationError,
    business_validation_exception_handler,
    internal_server_exception_handler,
)
from app.api.routes import router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    description="AI-powered revenue recovery decision engine.",
    version="0.1.0",
)


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# EXCEPTION HANDLERS
# --------------------------------------------------

app.add_exception_handler(
    BusinessValidationError,
    business_validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    internal_server_exception_handler,
)


# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

app.include_router(
    router,
    prefix="/api/v1",
)


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "RECLAIM AI Recovery Engine API is running",
        "status": "healthy",
        "environment": "development",
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "reclaim-backend",
        "environment": "development",
    }