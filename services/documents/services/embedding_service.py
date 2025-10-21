"""
Service for generating and managing embeddings.
"""

import hashlib
import numpy as np
from typing import List, Optional
import openai
from shared.config.settings import settings


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        """Initialize the embedding service."""
        self.client = None
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.client = openai

    async def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-ada-002"
    ) -> np.ndarray:
        """
        Generate embedding for a given text.

        Args:
            text: Text to generate embedding for
            model: OpenAI model to use

        Returns:
            Numpy array with embedding vector
        """
        if not self.client:
            # Return a mock embedding for development if no API key
            return self._generate_mock_embedding()

        try:
            response = await self.client.embeddings.create(
                input=text,
                model=model
            )

            embedding = response.data[0].embedding
            return np.array(embedding)

        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Fallback to mock embedding
            return self._generate_mock_embedding()

    def _generate_mock_embedding(self) -> np.ndarray:
        """
        Generate a mock embedding for development/testing.

        Returns:
            Random 1536-dimensional vector
        """
        return np.random.randn(1536).astype(np.float32)

    def hash_text(self, text: str) -> str:
        """
        Generate SHA256 hash of text for caching.

        Args:
            text: Text to hash

        Returns:
            Hex digest of hash
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002"
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts
            model: OpenAI model to use

        Returns:
            List of embedding vectors
        """
        if not self.client:
            return [self._generate_mock_embedding() for _ in texts]

        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=model
            )

            embeddings = [np.array(data.embedding) for data in response.data]
            return embeddings

        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return [self._generate_mock_embedding() for _ in texts]