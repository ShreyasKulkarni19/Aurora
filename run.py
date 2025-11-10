"""Simple script to run the QA service."""

import os
# Disable TensorFlow to avoid Keras 3 compatibility issues
# We only use PyTorch for sentence-transformers
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # Enable reload for development
        log_level=settings.log_level.lower()
    )

