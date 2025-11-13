"""Service for hybrid search combining embedding and keyword matching."""

import re
import os
import pickle
import hashlib
import numpy as np
from typing import List, Tuple, Dict, Set, Optional
from collections import Counter
from pathlib import Path
from datetime import datetime, timedelta
from app.models import Message
from app.services.embedding_service import EmbeddingService
from app.config import settings
from app.utils.exceptions import EmbeddingError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Cache configuration
EMBEDDING_CACHE_DIR = Path(".cache")
EMBEDDING_CACHE_FILE = EMBEDDING_CACHE_DIR / "embeddings_cache.pkl"


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
        
        # Embedding cache
        self._cached_embeddings: Optional[np.ndarray] = None
        self._cached_message_hashes: Optional[List[str]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=getattr(settings, 'embedding_cache_ttl_hours', 24))
        
        # Load cached embeddings if available
        self._load_embedding_cache()
        
        logger.info(
            "Initialized hybrid search",
            embedding_weight=self.embedding_weight,
            keyword_weight=self.keyword_weight,
            min_keyword_matches=self.min_keyword_matches,
            embeddings_cached=self._cached_embeddings is not None
        )
    
    def _generate_message_hash(self, message_text: str) -> str:
        """Generate a hash for a message to detect changes."""
        return hashlib.md5(message_text.encode('utf-8')).hexdigest()
    
    def _load_embedding_cache(self) -> None:
        """Load cached embeddings from disk if available and valid."""
        try:
            if EMBEDDING_CACHE_FILE.exists():
                with open(EMBEDDING_CACHE_FILE, 'rb') as f:
                    cache_data = pickle.load(f)
                
                cache_timestamp = datetime.fromisoformat(cache_data['timestamp'])
                cache_age = datetime.now() - cache_timestamp
                
                if cache_age < self._cache_ttl:
                    self._cached_embeddings = cache_data['embeddings']
                    self._cached_message_hashes = cache_data['message_hashes']
                    self._cache_timestamp = cache_timestamp
                    
                    logger.info(
                        f"Loaded embeddings cache with {self._cached_embeddings.shape[0]} embeddings "
                        f"(age: {cache_age.total_seconds():.0f}s)"
                    )
                else:
                    logger.debug(f"Embedding cache expired (age: {cache_age.total_seconds():.0f}s)")
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
            self._cached_embeddings = None
            self._cached_message_hashes = None
    
    def _save_embedding_cache(
        self, 
        embeddings: np.ndarray, 
        message_hashes: List[str]
    ) -> None:
        """Save embeddings to disk cache for faster future access."""
        try:
            # Create cache directory if it doesn't exist
            EMBEDDING_CACHE_DIR.mkdir(exist_ok=True)
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'embeddings': embeddings,
                'message_hashes': message_hashes,
                'model_name': self.embedding_service.model_name,
                'embedding_dim': embeddings.shape[1] if len(embeddings.shape) > 1 else 0
            }
            
            with open(EMBEDDING_CACHE_FILE, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"Saved embeddings cache with {len(embeddings)} embeddings")
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")
    
    def _get_or_compute_embeddings(
        self, 
        message_texts: List[str]
    ) -> np.ndarray:
        """Get embeddings from cache or compute them if needed."""
        # Generate hashes for current messages
        current_hashes = [self._generate_message_hash(text) for text in message_texts]
        
        # Check if we can use cached embeddings
        cache_valid = (
            self._cached_embeddings is not None and 
            self._cached_message_hashes is not None and
            len(current_hashes) == len(self._cached_message_hashes) and
            current_hashes == self._cached_message_hashes
        )
        
        if cache_valid:
            logger.info(
                f"Using cached embeddings for {len(message_texts)} messages "
                f"(saved ~{len(message_texts) * 0.5:.0f}s processing time)"
            )
            return self._cached_embeddings
        
        # Cache is invalid - detect why
        if self._cached_embeddings is not None:
            if len(current_hashes) != len(self._cached_message_hashes or []):
                logger.info(
                    f"Message count changed: {len(self._cached_message_hashes or [])} → {len(current_hashes)}. "
                    "Recomputing embeddings..."
                )
            else:
                logger.info(
                    "Message content changed. Recomputing embeddings..."
                )
        
        # Need to compute embeddings
        logger.info(
            f"Computing embeddings for {len(message_texts)} messages "
            "(this will be cached for future use)..."
        )
        
        embeddings = self.embedding_service.model.encode(
            message_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=32
        )
        
        # Cache the results
        self._cached_embeddings = embeddings
        self._cached_message_hashes = current_hashes
        self._cache_timestamp = datetime.now()
        
        # Save to disk
        self._save_embedding_cache(embeddings, current_hashes)
        
        logger.info("Embeddings computed and cached successfully")
        return embeddings
    
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
            
            # Generate or retrieve cached embeddings for all messages
            message_embeddings = self._get_or_compute_embeddings(message_texts)
            
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
