"""Custom exceptions for the QA service."""

from fastapi import HTTPException, status


class MessagesAPIError(HTTPException):
    """Exception raised when messages API fails."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Messages API error: {detail}"
        )


class EmbeddingError(HTTPException):
    """Exception raised when embedding generation fails."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding error: {detail}"
        )


class LLMError(HTTPException):
    """Exception raised when LLM generation fails."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM error: {detail}"
        )


class ValidationError(HTTPException):
    """Exception raised when validation fails."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

