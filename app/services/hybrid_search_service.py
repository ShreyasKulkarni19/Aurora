"""Service for hybrid search combining embedding and keyword matching."""

import re
import numpy as np
from typing import List, Tuple, Dict, Set
from collections import Counter
from app.models import Message
from app.services.embedding_service import EmbeddingService
from app.config import settings
from app.utils.exceptions import EmbeddingError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HybridSearchService:
    """Service for hybrid search using both embeddings and keyword matching."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.top_k = settings.top_k_messages
        
        # Hybrid search configuration
        self.embedding_weight = getattr(settings, 'embedding_weight', 0.7)  # Weight for embedding scores
        self.keyword_weight = getattr(settings, 'keyword_weight', 0.3)      # Weight for keyword scores
        self.min_keyword_matches = getattr(settings, 'min_keyword_matches', 1)  # Minimum keyword matches required
        
        # Keyword matching configuration
        self.use_stemming = getattr(settings, 'use_stemming', True)
        self.case_sensitive = getattr(settings, 'case_sensitive', False)
        
        logger.info(
            "Initialized hybrid search",
            embedding_weight=self.embedding_weight,
            keyword_weight=self.keyword_weight,
            min_keyword_matches=self.min_keyword_matches
        )
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Input text
            
        Returns:
            Set of keywords
        """
        if not text:
            return set()
        
        # Convert to lowercase if not case sensitive
        if not self.case_sensitive:
            text = text.lower()
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', text)
        
        # Filter out very short words and common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those', 'what', 'where', 'when',
            'why', 'how', 'who', 'which'
        }
        
        keywords = {
            word for word in words 
            if len(word) > 2 and word.lower() not in stop_words
        }
        
        return keywords
    
    def _compute_keyword_score(self, query_keywords: Set[str], message_text: str) -> float:
        """
        Compute keyword matching score for a message.
        
        Args:
            query_keywords: Set of keywords from the query
            message_text: Text of the message
            
        Returns:
            Keyword matching score between 0 and 1
        """
        if not query_keywords:
            return 0.0
        
        message_keywords = self._extract_keywords(message_text)
        
        if not message_keywords:
            return 0.0
        
        # Count keyword matches
        matches = query_keywords.intersection(message_keywords)
        
        if not matches:
            return 0.0
        
        # Calculate score based on:
        # 1. Number of matching keywords
        # 2. Proportion of query keywords that match
        # 3. Frequency of matches in the message
        
        match_count = len(matches)
        query_coverage = match_count / len(query_keywords)
        
        # Count frequency of matches in message text
        message_text_lower = message_text.lower() if not self.case_sensitive else message_text
        frequency_score = 0.0
        
        for keyword in matches:
            # Count occurrences of this keyword
            keyword_lower = keyword.lower() if not self.case_sensitive else keyword
            occurrences = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', message_text_lower))
            frequency_score += min(occurrences, 3) / 3.0  # Cap at 3 occurrences per keyword
        
        frequency_score = frequency_score / len(matches) if matches else 0.0
        
        # Combine scores
        keyword_score = (query_coverage * 0.6 + frequency_score * 0.4)
        
        return min(keyword_score, 1.0)
    
    def _compute_hybrid_scores(
        self,
        query: str,
        messages: List[Message],
        message_texts: List[str],
        embedding_scores: np.ndarray
    ) -> np.ndarray:
        """
        Compute hybrid scores combining embedding and keyword matching.
        
        Args:
            query: User's query
            messages: List of messages
            message_texts: List of formatted message texts
            embedding_scores: Array of embedding similarity scores
            
        Returns:
            Array of hybrid scores
        """
        # Extract keywords from query
        query_keywords = self._extract_keywords(query)
        
        logger.info(
            "Computing hybrid scores",
            query_keywords=list(query_keywords),
            num_messages=len(messages)
        )
        
        # Compute keyword scores for all messages
        keyword_scores = []
        messages_with_keywords = 0
        
        for message_text in message_texts:
            keyword_score = self._compute_keyword_score(query_keywords, message_text)
            keyword_scores.append(keyword_score)
            if keyword_score > 0:
                messages_with_keywords += 1
        
        keyword_scores = np.array(keyword_scores)
        
        logger.info(
            "Keyword matching results",
            messages_with_keywords=messages_with_keywords,
            avg_keyword_score=float(np.mean(keyword_scores)),
            max_keyword_score=float(np.max(keyword_scores))
        )
        
        # Normalize scores to [0, 1] range
        embedding_scores_norm = (embedding_scores + 1) / 2  # Convert from [-1, 1] to [0, 1]
        
        # Combine scores using weighted average
        hybrid_scores = (
            self.embedding_weight * embedding_scores_norm +
            self.keyword_weight * keyword_scores
        )
        
        # Apply keyword filter if specified
        if self.min_keyword_matches > 0 and query_keywords:
            # Only keep messages that have at least min_keyword_matches
            keyword_mask = keyword_scores >= (self.min_keyword_matches / len(query_keywords))
            
            # If no messages meet the keyword threshold, fallback to pure embedding
            if not np.any(keyword_mask):
                logger.warning(
                    "No messages meet keyword threshold, falling back to embedding-only search"
                )
                hybrid_scores = embedding_scores_norm
            else:
                # Set non-matching messages to low score
                hybrid_scores = np.where(keyword_mask, hybrid_scores, hybrid_scores * 0.1)
        
        return hybrid_scores
    
    def retrieve_relevant_messages(
        self,
        question: str,
        messages: List[Message],
        message_texts: List[str]
    ) -> List[Tuple[Message, float]]:
        """
        Retrieve top-k most relevant messages using hybrid search.
        
        Args:
            question: User's question
            messages: List of all messages
            message_texts: List of formatted message texts
            
        Returns:
            List of tuples (message, hybrid_score) sorted by relevance
        """
        try:
            logger.info(
                "Starting hybrid search",
                question=question,
                total_messages=len(messages),
                top_k=self.top_k
            )
            
            # Step 1: Get embedding scores
            logger.info("Step 1/3: Computing embedding similarities...")
            query_embedding = self.embedding_service.generate_embedding(question)
            
            # Generate embeddings for all messages
            message_embeddings = self.embedding_service.model.encode(
                message_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=True,
                batch_size=32
            )
            
            # Compute embedding similarities
            embedding_scores = self.embedding_service.compute_similarity(
                query_embedding,
                message_embeddings
            )
            
            logger.info("Step 2/3: Computing keyword matches...")
            
            # Step 2: Compute hybrid scores
            hybrid_scores = self._compute_hybrid_scores(
                question, messages, message_texts, embedding_scores
            )
            
            logger.info("Step 3/3: Ranking results...")
            
            # Step 3: Get top-k results
            top_indices = np.argsort(hybrid_scores)[::-1][:self.top_k]
            
            results = [
                (messages[idx], float(hybrid_scores[idx]))
                for idx in top_indices
            ]
            
            # Log detailed results
            logger.info(
                "Hybrid search completed",
                count=len(results),
                top_score=results[0][1] if results else 0.0,
                top_embedding_score=float(embedding_scores[top_indices[0]]) if results else 0.0
            )
            
            # Log top few results for debugging
            for i, (msg, score) in enumerate(results[:3]):
                idx = top_indices[i]
                logger.debug(
                    f"Result {i+1}",
                    hybrid_score=score,
                    embedding_score=float(embedding_scores[idx]),
                    message_preview=message_texts[idx][:100] + "..."
                )
            
            return results
            
        except Exception as e:
            logger.error(
                "Failed to retrieve relevant messages with hybrid search",
                error=str(e),
                error_type=type(e).__name__
            )
            raise EmbeddingError(f"Hybrid search failed: {str(e)}")
