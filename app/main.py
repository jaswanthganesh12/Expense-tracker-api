import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.database import Base, engine
from app.routers import expense, user
from app.utils.config import settings

# ─────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────
# Rate Limiter
# ─────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

# ─────────────────────────────────────────────────
# FastAPI Application
# ─────────────────────────────────────────────────

app = FastAPI(
    title="Expense Tracker API",
    description=(
        "A production-ready REST API for tracking personal expenses. "
        "Features user authentication, expense CRUD, smart filtering, "
        "analytics, and pagination."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Expense Tracker API",
    },
    license_info={
        "name": "MIT",
    },
)

# Attach rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─────────────────────────────────────────────────
# CORS Middleware
# ─────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────
# Global Exception Handler
# ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a clean 500 response."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
    )


# ─────────────────────────────────────────────────
# Database Table Creation
# ─────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    """Create all database tables on application startup."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")
    logger.info(f"API documentation available at /docs and /redoc")


# ─────────────────────────────────────────────────
# Include Routers
# ─────────────────────────────────────────────────

app.include_router(user.router)
app.include_router(expense.router)


# ─────────────────────────────────────────────────
# Root Endpoint
# ─────────────────────────────────────────────────

@app.get(
    "/",
    tags=["Root"],
    summary="API Health Check",
    description="Root endpoint to verify the API is running.",
)
def root():
    """Return a welcome message and basic API info."""
    return {
        "message": "Welcome to the Expense Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get(
    "/health",
    tags=["Root"],
    summary="Health Check",
    description="Health check endpoint for monitoring and load balancers.",
)
def health_check():
    """Return API health status."""
    return {"status": "healthy"}
