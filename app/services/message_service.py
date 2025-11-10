"""Service for fetching and managing messages from the messages API."""

import httpx
from typing import List
from app.models import Message, MessagesResponse
from app.config import settings
from app.utils.exceptions import MessagesAPIError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MessageService:
    """Service for interacting with the messages API."""
    
    def __init__(self):
        # Keep the URL as configured - the API requires the trailing slash
        self.api_url = settings.messages_api_url
        self.timeout = settings.messages_api_timeout
        self.page_size = settings.messages_page_size
        
        # Configure client to follow redirects and set proper headers
        # httpx 0.25.2 supports follow_redirects parameter
        # Use try-except for compatibility with different httpx versions
        try:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,  # Follow redirects (307, 301, etc.) - required for this API
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Aurora-QA-Service/1.0"
                }
            )
        except TypeError:
            # Fallback for older httpx versions that don't support follow_redirects
            # In this case, redirects will be handled manually if needed
            logger.warning("httpx version doesn't support follow_redirects, using default client")
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Aurora-QA-Service/1.0"
                }
            )
    
    async def fetch_all_messages(self) -> List[Message]:
        """
        Fetch all messages from the messages API with pagination support.
        
        Returns:
            List of Message objects
            
        Raises:
            MessagesAPIError: If the API request fails
        """
        all_messages = []
        skip = 0
        total_messages = None
        
        try:
            logger.info("Fetching messages from API", url=self.api_url)
            
            while True:
                # Fetch a page of messages
                params = {
                    "skip": skip,
                    "limit": self.page_size
                }
                
                logger.debug(
                    "Fetching messages page",
                    skip=skip,
                    limit=self.page_size
                )
                
                # Make request - handle redirects manually if follow_redirects didn't work
                max_redirects = 5
                redirect_count = 0
                current_url = self.api_url
                current_params = params.copy()  # Preserve original params
                response = None
                
                while redirect_count < max_redirects:
                    logger.info(f"Making request to: {current_url} with params: {current_params}")
                    response = await self.client.get(current_url, params=current_params)
                    
                    # Log response details for debugging
                    logger.info(
                        "API response received",
                        status_code=response.status_code,
                        url=str(response.url),
                        headers=dict(response.headers)
                    )
                    
                    # Handle redirects manually if client didn't follow them
                    if response.status_code in (301, 302, 307, 308):
                        redirect_count += 1
                        location = response.headers.get("Location")
                        if location:
                            logger.info(f"Following redirect {redirect_count}/{max_redirects} to: {location}")
                            # Handle relative redirects
                            if location.startswith('/'):
                                from urllib.parse import urljoin
                                location = urljoin(str(response.url), location)
                            current_url = location
                            # Keep params for redirect (query parameters should be preserved)
                            continue
                        else:
                            raise MessagesAPIError("Redirect response without Location header")
                    
                    # Check status and raise error with details if not successful
                    if response.status_code != 200:
                        error_text = response.text[:500]  # Limit error text length
                        logger.error(
                            "API returned error status",
                            status_code=response.status_code,
                            url=str(response.url),
                            error_text=error_text,
                            response_headers=dict(response.headers)
                        )
                        
                        # Special handling for payment/quota errors
                        if response.status_code == 402:
                            raise MessagesAPIError(
                                f"Payment required (HTTP 402): The messages API requires payment or has reached quota limits. Response: {error_text}"
                            )
                        elif response.status_code == 429:
                            raise MessagesAPIError(
                                f"Rate limit exceeded (HTTP 429): The messages API is rate limiting requests. Response: {error_text}"
                            )
                        else:
                            raise MessagesAPIError(
                                f"HTTP {response.status_code}: {error_text}"
                            )
                    
                    # Success - break out of redirect loop
                    break
                
                if redirect_count >= max_redirects:
                    raise MessagesAPIError(f"Too many redirects (>{max_redirects})")
                
                if response is None:
                    raise MessagesAPIError("No response received from API")
                
                data = response.json()
                
                # Parse response as PaginatedMessages
                messages_response = MessagesResponse(**data)
                
                # Set total on first request
                if total_messages is None:
                    total_messages = messages_response.total
                    logger.info(
                        "Total messages available",
                        total=total_messages
                    )
                
                # Add messages from this page
                all_messages.extend(messages_response.items)
                
                logger.debug(
                    "Fetched messages page",
                    page_messages=len(messages_response.items),
                    total_fetched=len(all_messages),
                    total_available=total_messages
                )
                
                # Check if we've fetched all messages
                if len(all_messages) >= total_messages:
                    break
                
                # Check if this was the last page (fewer messages than page size)
                if len(messages_response.items) < self.page_size:
                    break
                
                # Move to next page
                skip += self.page_size
            
            logger.info(
                "Successfully fetched all messages",
                count=len(all_messages),
                total=total_messages
            )
            return all_messages
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching messages",
                status_code=e.response.status_code,
                error=str(e)
            )
            raise MessagesAPIError(
                f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching messages",
                error=str(e)
            )
            raise MessagesAPIError(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(
                "Unexpected error fetching messages",
                error=str(e),
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

