"""Configuration management for the QA service."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_title: str = "Aurora QA Service"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Messages API Configuration
    messages_api_url: str = Field(
        default="https://november7-730026606190.europe-west1.run.app/messages",
        description="URL of the messages API endpoint"
    )
    messages_api_timeout: int = Field(
        default=30,
        description="Timeout for messages API requests in seconds"
    )
    messages_page_size: int = Field(
        default=100,
        description="Number of messages to fetch per page (API default is 100)"
    )
    messages_request_delay: float = Field(
        default=0.3,
        description="Delay in seconds between paginated requests to avoid rate limiting"
    )
    
    # Embedding Configuration
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings"
    )
    embedding_device: str = Field(
        default="cpu",
        description="Device for embedding model (cpu/cuda)"
    )
    top_k_messages: int = Field(
        default=5,
        description="Number of top relevant messages to retrieve"
    )
    
    # Hybrid Search Configuration
    embedding_weight: float = Field(
        default=0.7,
        description="Weight for embedding scores in hybrid search (0.0 to 1.0)"
    )
    keyword_weight: float = Field(
        default=0.3,
        description="Weight for keyword scores in hybrid search (0.0 to 1.0)"
    )
    min_keyword_matches: int = Field(
        default=1,
        description="Minimum number of keyword matches required for relevance"
    )
    use_stemming: bool = Field(
        default=True,
        description="Whether to use stemming for keyword matching"
    )
    case_sensitive: bool = Field(
        default=False,
        description="Whether keyword matching should be case sensitive"
    )
    
    # Cache Configuration
    embedding_cache_ttl_hours: int = Field(
        default=24,
        description="Time-to-live for embedding cache in hours"
    )
    message_cache_ttl_minutes: int = Field(
        default=5,
        description="Time-to-live for message cache in minutes"
    )
    
    # LLM Configuration
    llm_provider: str = Field(
        default="openai",
        description="LLM provider (openai, anthropic, local)"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model name"
    )
    openai_temperature: float = Field(
        default=0.1,
        description="Temperature for LLM generation"
    )
    openai_max_tokens: int = Field(
        default=200,
        description="Maximum tokens for LLM response"
    )
    
    # Anthropic Configuration (alternative)
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-opus-20240229",
        description="Anthropic model name"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

