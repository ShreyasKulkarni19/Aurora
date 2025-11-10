"""Service for generating embeddings and semantic retrieval."""

import os
# Disable TensorFlow to avoid Keras 3 compatibility issues
# We only use PyTorch for sentence-transformers
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from app.models import Message
from app.config import settings
from app.utils.exceptions import EmbeddingError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings and performing semantic search."""
    
    def __init__(self):
        self.model_name = settings.embedding_model
        self.device = settings.embedding_device
        self.top_k = settings.top_k_messages
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            logger.info(
                "Loading embedding model",
                model=self.model_name,
                device=self.device
            )
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device
            )
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(
                "Failed to load embedding model",
                error=str(e),
                error_type=type(e).__name__
            )
            raise EmbeddingError(f"Failed to load model: {str(e)}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a text string.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            if not text or not text.strip():
                # Return zero vector for empty text
                return np.zeros(self.model.get_sentence_embedding_dimension())
            
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding
        except Exception as e:
            logger.error(
                "Failed to generate embedding",
                error=str(e),
                text_length=len(text)
            )
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}")
    
    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and documents.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: Document embedding matrix
            
        Returns:
            Array of similarity scores
        """
        # Cosine similarity (dot product since embeddings are normalized)
        similarities = np.dot(document_embeddings, query_embedding)
        return similarities
    
    def retrieve_relevant_messages(
        self,
        question: str,
        messages: List[Message],
        message_texts: List[str]
    ) -> List[Tuple[Message, float]]:
        """
        Retrieve top-k most relevant messages for a question.
        
        Args:
            question: User's question
            messages: List of all messages
            message_texts: List of formatted message texts
            
        Returns:
            List of tuples (message, similarity_score) sorted by relevance
        """
        try:
            logger.info(
                "Retrieving relevant messages",
                question=question,
                total_messages=len(messages),
                top_k=self.top_k
            )
            
            # Generate query embedding
            query_embedding = self.generate_embedding(question)
            
            # Generate embeddings for all messages
            message_embeddings = self.model.encode(
                message_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            # Compute similarities
            similarities = self.compute_similarity(
                query_embedding,
                message_embeddings
            )
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:self.top_k]
            
            # Return top-k messages with scores
            results = [
                (messages[idx], float(similarities[idx]))
                for idx in top_indices
            ]
            
            logger.info(
                "Retrieved relevant messages",
                count=len(results),
                top_score=results[0][1] if results else 0.0
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Failed to retrieve relevant messages",
                error=str(e),
                error_type=type(e).__name__
            )
            raise EmbeddingError(f"Failed to retrieve messages: {str(e)}")

