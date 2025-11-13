"""Main QA service that orchestrates the question answering pipeline."""

from typing import List, Tuple
from app.models import Message
from app.services.message_service import MessageService
from app.services.hybrid_search_service import HybridSearchService
from app.services.llm_service import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QAService:
    """Main service for question answering."""
    
    def __init__(self):
        self.message_service = MessageService()
        self.hybrid_search_service = HybridSearchService()
        self.llm_service = LLMService()
    
    async def answer_question(self, question: str) -> Tuple[str, List[str]]:
        """
        Answer a question using RAG pipeline.
        
        Args:
            question: User's natural language question
            
        Returns:
            Tuple of (answer, source_message_ids)
        """
        try:
            logger.info("Processing question", question=question)
            
            # Step 1: Fetch all messages
            logger.info("Step 1/4: Fetching messages from API...")
            messages = await self.message_service.fetch_all_messages()
            logger.info(f"Step 1/4: Fetched {len(messages)} messages")
            
            if not messages:
                logger.warning("No messages found")
                return (
                    "I could not find any messages to answer your question.",
                    []
                )
            
            # Step 2: Format messages for embedding
            logger.info("Step 2/4: Formatting messages for embedding...")
            message_texts = [
                self.message_service.format_message_text(msg)
                for msg in messages
            ]
            
            # Step 3: Retrieve relevant messages using hybrid search
            logger.info("Step 3/4: Finding relevant messages using hybrid search...")
            relevant_messages = self.hybrid_search_service.retrieve_relevant_messages(
                question=question,
                messages=messages,
                message_texts=message_texts
            )
            logger.info(f"Step 3/4: Found {len(relevant_messages)} relevant messages")
            
            if not relevant_messages:
                logger.warning("No relevant messages found")
                return (
                    "I could not find relevant information to answer your question.",
                    []
                )
            
            # Step 4: Generate answer using LLM
            logger.info("Step 4/4: Generating answer using LLM...")
            answer = await self.llm_service.generate_answer(
                question=question,
                relevant_messages=relevant_messages
            )
            logger.info("Step 4/4: Answer generated successfully")
            
            # Step 5: Extract source message IDs
            source_ids = [
                msg.id if msg.id else f"msg_{idx}"
                for idx, (msg, _) in enumerate(relevant_messages)
            ]
            
            logger.info(
                "Successfully generated answer",
                question=question,
                answer_length=len(answer),
                num_sources=len(source_ids)
            )
            
            return answer, source_ids
            
        except Exception as e:
            logger.error(
                "Error processing question",
                question=question,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def close(self):
        """Clean up resources."""
        await self.message_service.close()

