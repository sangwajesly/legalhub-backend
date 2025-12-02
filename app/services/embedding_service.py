"""
Service for semantic chunking and embedding generation for RAG.
"""

from typing import List, Dict, Any
from transformers import AutoTokenizer, AutoModel
import torch
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Handles semantic chunking and embedding generation for text.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initializes the tokenizer and model for embedding generation.
        """
        self.model_name = model_name
        # Defer heavy model loading until actually needed (lazy load)
        self.tokenizer = None
        self.model = None

    def _mean_pooling(self, model_output, attention_mask):
        """
        Performs mean pooling to get sentence embeddings.
        """
        token_embeddings = model_output[
            0
        ]  # First element of model_output contains all token embeddings
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a dense vector embedding for a given text.
        """
        if not text:
            return []

        # Lazy-load tokenizer and model to avoid import-time heavy downloads
        if self.tokenizer is None or self.model is None:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name)
                self.model.eval()
            except Exception as e:
                logger.error("Failed to load embedding model: %s", e)
                raise

        encoded_input = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=getattr(self.tokenizer, "model_max_length", 512),
        )

        with torch.no_grad():
            model_output = self.model(**encoded_input)

        sentence_embedding = self._mean_pooling(
            model_output, encoded_input["attention_mask"]
        )
        # Normalize embeddings
        sentence_embedding = torch.nn.functional.normalize(
            sentence_embedding, p=2, dim=1
        )
        return sentence_embedding[0].tolist()

    def semantic_chunk_text(
        self,
        text: str,
        min_chunk_size: int = 200,
        max_chunk_size: int = 500,
        overlap_ratio: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """
        Splits text into semantically meaningful chunks with configurable overlap,
        prioritizing sentence boundaries.

        Args:
            text: The input text content.
            min_chunk_size: Minimum number of characters for a chunk.
            max_chunk_size: Maximum number of characters for a chunk.
            overlap_ratio: Ratio of overlap between consecutive chunks.

        Returns:
            A list of dictionaries, where each dictionary represents a chunk
            and contains 'content' and potentially other metadata.
        """
        if not text:
            return []

        # Simple sentence tokenization
        sentences = text.split(". ")  # Basic split, could use NLTK for better results
        if not sentences:
            return [{"content": text}]

        chunks = []
        current_chunk_sentences = []
        current_chunk_length = 0

        for i, sentence in enumerate(sentences):
            # Add back the period for the current sentence
            sentence_with_period = sentence + (". " if i < len(sentences) - 1 else "")
            sentence_length = len(sentence_with_period)

            # If adding the current sentence exceeds max_chunk_size,
            # or if the current chunk is long enough and we are at a natural break
            if (
                current_chunk_length + sentence_length > max_chunk_size
                and current_chunk_sentences
            ) or (
                current_chunk_length >= min_chunk_size
                and sentence_length > 0
                and len(current_chunk_sentences) > 0
            ):

                # Form the chunk
                chunk_content = "".join(current_chunk_sentences).strip()
                if chunk_content:
                    chunks.append({"content": chunk_content})

                # Prepare for next chunk with overlap
                overlap_length = int(max_chunk_size * overlap_ratio)
                overlap_text = (
                    chunk_content[-overlap_length:]
                    if len(chunk_content) > overlap_length
                    else ""
                )

                current_chunk_sentences = (
                    [overlap_text + sentence_with_period]
                    if overlap_text
                    else [sentence_with_period]
                )
                current_chunk_length = len("".join(current_chunk_sentences))
            else:
                current_chunk_sentences.append(sentence_with_period)
                current_chunk_length += sentence_length

        # Add the last chunk if any content remains
        final_chunk_content = "".join(current_chunk_sentences).strip()
        if final_chunk_content:
            chunks.append({"content": final_chunk_content})

        return chunks

    # Hierarchical chunking (Placeholder for future, more complex implementation)
    def hierarchical_chunking(
        self, text: str, headings: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Placeholder for more advanced hierarchical chunking based on document structure.
        """
        # For now, just defer to semantic_chunk_text
        return self.semantic_chunk_text(text)


# Do not instantiate a global EmbeddingService here to avoid heavy import-time work.
