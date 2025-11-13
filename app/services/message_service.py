"""Service for fetching and managing messages from the messages API."""

import httpx
import asyncio
import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.models import Message, MessagesResponse
from app.config import settings
from app.utils.exceptions import MessagesAPIError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Persistent cache file path
CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "messages_cache.json"


class MessageService:
    """Service for interacting with the messages API."""
    
    def __init__(self):
        # Normalize URL - remove trailing slash
        self.api_url = settings.messages_api_url.rstrip('/')
        self.timeout = settings.messages_api_timeout
        self.page_size = settings.messages_page_size
        self.request_delay = settings.messages_request_delay
        
        # Cache for messages to avoid fetching on every request
        self._cached_messages: Optional[List[Message]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
        
        # Load cache from disk if available
        self._load_cache_from_disk()
        
        # Configure client with connection limits and proper headers
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0
            ),
            headers={
                "Accept": "application/json",
                "User-Agent": "Aurora-QA-Service/1.0"
            }
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        reraise=True
    )
    async def _fetch_page(self, skip: int, limit: int) -> MessagesResponse:
        """
        Fetch a single page of messages with retry logic.
        
        Args:
            skip: Number of messages to skip
            limit: Number of messages to fetch
            
        Returns:
            MessagesResponse object
        """
        params = {
            "skip": skip,
            "limit": limit
        }
        
        logger.debug(f"Fetching page: skip={skip}, limit={limit}")
        
        try:
            response = await self.client.get(self.api_url, params=params)
            
            # Log response for debugging
            logger.debug(
                "API response",
                status_code=response.status_code,
                url=str(response.url)
            )
            
            # Check for client errors (4xx) - some might be retryable
            if response.status_code in (400, 401, 402, 403):
                error_text = response.text[:500]
                logger.warning(
                    f"Received {response.status_code} error, will retry",
                    url=str(response.url),
                    error_text=error_text
                )
                # Raise HTTPStatusError to trigger retry
                response.raise_for_status()
            
            # Ensure status is OK (for non-4xx errors)
            if response.status_code != 200:
                response.raise_for_status()
            data = response.json()
            return MessagesResponse(**data)
            
        except httpx.HTTPStatusError as e:
            # Log the error but let retry decorator handle it
            status_code = e.response.status_code if e.response else "unknown"
            logger.warning(
                f"HTTP error {status_code} on attempt, will retry",
                url=str(e.request.url) if hasattr(e, 'request') and hasattr(e.request, 'url') else self.api_url
            )
            raise
        except httpx.RequestError as e:
            logger.warning(f"Request error, will retry: {str(e)}")
            raise
    
    def _load_cache_from_disk(self) -> None:
        """Load cached messages from disk if available and valid."""
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_timestamp = datetime.fromisoformat(cache_data['timestamp'])
                cache_age = datetime.now() - cache_timestamp
                
                if cache_age < self._cache_ttl:
                    # Load messages from cache
                    messages_data = cache_data['messages']
                    self._cached_messages = [Message(**msg) for msg in messages_data]
                    self._cache_timestamp = cache_timestamp
                    logger.info(
                        f"Loaded {len(self._cached_messages)} messages from cache "
                        f"(age: {cache_age.total_seconds():.0f}s)"
                    )
                else:
                    logger.debug(f"Cache expired (age: {cache_age.total_seconds():.0f}s)")
        except Exception as e:
            logger.warning(f"Failed to load cache from disk: {e}")
            self._cached_messages = None
            self._cache_timestamp = None
    
    def _save_cache_to_disk(self, messages: List[Message]) -> None:
        """Save cached messages to disk for persistence across runs."""
        try:
            # Create cache directory if it doesn't exist
            CACHE_DIR.mkdir(exist_ok=True)
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'messages': [msg.model_dump() for msg in messages]
            }
            
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Saved {len(messages)} messages to disk cache")
        except Exception as e:
            logger.warning(f"Failed to save cache to disk: {e}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cached messages are still valid."""
        if self._cached_messages is None or self._cache_timestamp is None:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    async def fetch_all_messages(self, force_refresh: bool = False) -> List[Message]:
        """
        Fetch all messages from the messages API with pagination support.
        Includes delays between requests to avoid rate limiting.
        Messages are cached for 5 minutes to improve performance.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            List of Message objects
            
        Raises:
            MessagesAPIError: If the API request fails
        """
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            logger.info(f"Using cached messages ({len(self._cached_messages)} messages)")
            return self._cached_messages
        
        all_messages = []
        skip = 0
        total_messages = None
        
        try:
            logger.info(f"Fetching messages from API: {self.api_url}")
            
            while True:
                # Fetch page with retry logic
                messages_response = await self._fetch_page(skip, self.page_size)
                
                # Set total on first request
                if total_messages is None:
                    total_messages = messages_response.total
                    logger.info(f"Total messages available: {total_messages}")
                
                # Add messages from this page
                all_messages.extend(messages_response.items)
                
                # Log progress every 10 pages to show activity
                page_num = (skip // self.page_size) + 1
                if page_num % 10 == 0 or len(all_messages) >= total_messages:
                    logger.info(
                        f"Progress: {len(all_messages)}/{total_messages} messages fetched "
                        f"(page {page_num})"
                    )
                
                logger.debug(
                    f"Fetched {len(messages_response.items)} messages, "
                    f"total: {len(all_messages)}/{total_messages}"
                )
                
                # Check if we've fetched all messages
                if len(all_messages) >= total_messages or len(messages_response.items) < self.page_size:
                    break
                
                # Move to next page
                skip += self.page_size
                
                # Add delay between requests to avoid rate limiting
                # Small delay: 0.1-0.3 seconds between requests
                if self.request_delay > 0:
                    await asyncio.sleep(self.request_delay)
            
            logger.info(f"Successfully fetched {len(all_messages)} messages")
            
            # Update in-memory cache
            self._cached_messages = all_messages
            self._cache_timestamp = datetime.now()
            
            # Save to disk for persistence across runs
            self._save_cache_to_disk(all_messages)
            
            return all_messages
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:500] if e.response else "No response"
            status_code = e.response.status_code if e.response else "unknown"
            logger.error(
                f"HTTP error fetching messages: {status_code} - {error_text}",
                status_code=status_code,
                url=str(e.request.url) if hasattr(e, 'request') and hasattr(e.request, 'url') else self.api_url
            )
            raise MessagesAPIError(f"HTTP {status_code}: {error_text}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching messages: {e}")
            raise MessagesAPIError(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected error fetching messages: {e}",
                error_type=type(e).__name__
            )
            raise MessagesAPIError(f"Unexpected error: {str(e)}")
    
    def format_message_text(self, message: Message) -> str:
        """
        Format a message into a searchable text string.
        
        Args:
            message: Message object to format
            
        Returns:
            Formatted text string
        """
        parts = []
        
        if message.user_name:
            parts.append(f"From: {message.user_name}")
        if message.user_id:
            parts.append(f"User ID: {message.user_id}")
        if message.message:
            parts.append(f"Message: {message.message}")
        if message.timestamp:
            parts.append(f"Time: {message.timestamp}")
        
        return " | ".join(parts)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
