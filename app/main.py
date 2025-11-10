"""Main application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api.routes import router, set_qa_service
from app.services.qa_service import QAService
from app.utils.logger import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Global QA service instance
qa_service: QAService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global qa_service
    
    # Startup
    logger.info("Starting Aurora QA Service")
    qa_service = QAService()
    set_qa_service(qa_service)
    logger.info("QA Service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aurora QA Service")
    if qa_service:
        await qa_service.close()
    logger.info("QA Service shut down")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Production-grade Question Answering API using RAG",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    router,
    prefix=settings.api_prefix,
    tags=["QA"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Aurora QA Service",
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )

