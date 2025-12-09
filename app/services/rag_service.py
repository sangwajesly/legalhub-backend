"""
RAG (Retrieval-Augmented Generation) Service

This service orchestrates the RAG pipeline:
1. Retrieves relevant documents from FAISS vector store based on user query
2. Augments the LLM prompt with retrieved context
3. Generates responses using the augmented prompt
4. Manages the integration between embeddings, vector store, and LLM
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, UTC

from app.config import settings
from app.services import firebase_service, gemini_service
from app.utils.faiss_store import get_vector_store

from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service for LegalHub.
    
    Provides methods for:
    - Ingesting documents into FAISS vector store
    - Retrieving relevant documents based on queries
    - Augmenting prompts with retrieved context
    - Generating RAG-enhanced responses
    """

    def __init__(self, collection_name: str = "legalhub_documents"):
        """
        Initialize RAG service.
        
        Args:
            collection_name: Name of the FAISS collection to use
        """
        self.collection_name = collection_name
        self._initialize_collection()

    def _initialize_collection(self):
        """Initialize or get the FAISS vector store."""
        try:
            self.vector_store = get_vector_store(self.collection_name)
            logger.info(f"RAG collection '{self.collection_name}' initialized with FAISS")
            print(f"[OK] FAISS vector store initialized: {self.vector_store.count()} documents")
        except Exception as e:
            logger.error(f"Failed to initialize RAG collection: {e}")
            raise

    async def add_documents(
        self,
        documents: List[Dict[str, str]],
        metadata: Optional[Dict] = None
    ) -> Dict[str, int]:
        """
        Add documents to the RAG vector store.
        
        Args:
            documents: List of document dicts with 'id', 'content', 'source'
            metadata: Optional metadata to attach to all documents
            
        Returns:
            Dict with counts of added documents
        """
        try:
            # FAISS add_documents is synchronous, run in thread pool
            result = await asyncio.to_thread(
                self.vector_store.add_documents,
                documents
            )
            logger.info(f"Added {result.get('added', 0)} documents to FAISS vector store")
            return result

        except Exception as e:
            logger.error(f"Error adding documents to RAG: {e}")
            raise

    async def retrieve_documents(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Retrieve relevant documents from the vector store.
        
        Args:
            query: The search query
            top_k: Number of top results to return
            score_threshold: Minimum similarity score for results
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        try:
            # FAISS search is synchronous, run in thread pool
            results = await asyncio.to_thread(
                self.vector_store.search,
                query,
                top_k
            )

            # Filter by score threshold
            documents = [doc for doc in results if doc.get('score', 0) >= score_threshold]

            logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents from RAG: {e}")
            return []

    async def augment_prompt(
        self,
        user_query: str,
        retrieved_docs: List[Dict],
        max_context_length: int = 2000
    ) -> str:
        """
        Augment the user query with retrieved document context.
        
        Args:
            user_query: Original user query
            retrieved_docs: List of retrieved documents
            max_context_length: Maximum length of context to include
            
        Returns:
            Augmented prompt with RAG context
        """
        if not retrieved_docs:
            return user_query

        # Build context from retrieved documents
        context_parts = []
        total_length = 0

        for doc in retrieved_docs:
            content = doc.get("content", "")
            score = doc.get("score", 0)
            # Source can be in doc directly or in metadata
            source = doc.get("source") or doc.get("metadata", {}).get("source", "unknown")
            
            # Format context chunk
            chunk = f"[Source: {source} (relevance: {score:.2f})]\n{content}\n"
            chunk_length = len(chunk)

            if total_length + chunk_length > max_context_length:
                break

            context_parts.append(chunk)
            total_length += chunk_length

        # Construct augmented prompt
        context = "\n".join(context_parts)
        augmented_prompt = f"""You are a legal assistant. Use the following context from legal documents to answer the user's question.

LEGAL CONTEXT:
{context}

USER QUESTION: {user_query}

INSTRUCTIONS:
- Base your answer on the provided legal context
- If the context doesn't contain relevant information, state that clearly
- Provide accurate legal information based on the documents
- When uncertain, recommend consulting with a qualified lawyer"""

        return augmented_prompt

    async def generate_rag_response(
        self,
        session_id: Optional[str],
        user_id: Optional[str],
        user_message: str,
        use_rag: bool = True,
        top_k: int = 3
    ) -> Tuple[str, List[Dict]]:
        """
        Generate a RAG-augmented response.
        
        Args:
            session_id: Chat session ID
            user_id: User ID
            user_message: User's message/query
            use_rag: Whether to use RAG enhancement
            top_k: Number of top documents to retrieve
            
        Returns:
            Tuple of (response_text, retrieved_documents)
        """
        retrieved_docs = []

        try:
            # 1. Persist user message
            if session_id:
                user_chat_message = ChatMessage(
                    role="user",
                    text=user_message,
                    userId=user_id,
                    createdAt=datetime.now(UTC)
                )
                await firebase_service.add_chat_message(session_id, user_chat_message)

            # 2. Retrieve relevant documents if RAG is enabled
            if use_rag:
                retrieved_docs = await self.retrieve_documents(
                    user_message,
                    top_k=top_k
                )

            # 3. Build augmented prompt
            if retrieved_docs and use_rag:
                final_prompt = await self.augment_prompt(user_message, retrieved_docs)
            else:
                # Fallback to chat history context if no RAG docs
                final_prompt = await self._build_chat_context_prompt(
                    session_id, user_message
                )

            # 4. Generate response using LLM
            try:
                ai_result = await gemini_service.send_message(final_prompt)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return "I'm sorry, I couldn't process that right now. Please try again later.", retrieved_docs

            # 5. Normalize reply
            reply = ai_result.get("response", str(ai_result)) if isinstance(ai_result, dict) else str(ai_result)
            if not reply:
                reply = ""

            # 6. Persist assistant message
            if session_id:
                assistant_chat_message = ChatMessage(
                    role="assistant",
                    text=reply,
                    userId=user_id,
                    createdAt=datetime.now(UTC)
                )
                await firebase_service.add_chat_message(session_id, assistant_chat_message)

            return reply, retrieved_docs

        except Exception as e:
            logger.error(f"Error in RAG response generation: {e}")
            return "An error occurred while processing your request.", retrieved_docs

    async def generate_rag_response_stream(
        self,
        session_id: Optional[str],
        user_id: Optional[str],
        user_message: str,
        use_rag: bool = True,
        top_k: int = 3
    ):
        """
        Generate a streaming RAG-augmented response.
        
        Yields response chunks as they become available.
        """
        retrieved_docs = []

        try:
            # 1. Persist user message
            if session_id:
                user_chat_message = ChatMessage(
                    role="user",
                    text=user_message,
                    userId=user_id,
                    createdAt=datetime.now(UTC)
                )
                await firebase_service.add_chat_message(session_id, user_chat_message)

            # 2. Retrieve relevant documents if RAG is enabled
            if use_rag:
                retrieved_docs = await self.retrieve_documents(
                    user_message,
                    top_k=top_k
                )

            # 3. Build augmented prompt
            if retrieved_docs and use_rag:
                final_prompt = await self.augment_prompt(user_message, retrieved_docs)
            else:
                final_prompt = await self._build_chat_context_prompt(
                    session_id, user_message
                )

            # 4. Stream response from LLM
            final_parts = []
            try:
                async for chunk in gemini_service.stream_send_message(final_prompt):
                    text = chunk.get("response", "") if isinstance(chunk, dict) else str(chunk)
                    final_parts.append(text)
                    yield text
            except Exception as e:
                logger.error(f"Streaming LLM call failed: {e}")
                yield ""

            # 5. Persist final assembled reply
            final_reply = "".join(final_parts)
            if session_id:
                assistant_chat_message = ChatMessage(
                    role="assistant",
                    text=final_reply,
                    userId=user_id,
                    createdAt=datetime.now(UTC)
                )
                await firebase_service.add_chat_message(session_id, assistant_chat_message)

        except Exception as e:
            logger.error(f"Error in streaming RAG response generation: {e}")
            yield ""

    async def _build_chat_context_prompt(
        self,
        session_id: Optional[str],
        user_message: str,
        max_messages: int = 5
    ) -> str:
        """
        Build a prompt using chat history context (fallback when no RAG docs).
        """
        context = []
        
        if session_id:
            try:
                msgs = await firebase_service.get_chat_history(session_id)
                msgs = msgs[-max_messages:] if msgs else []
                context = [f"{m.role}: {m.text}" for m in msgs if m]
            except Exception as e:
                logger.warning(f"Failed to load chat history: {e}")

        system = (
            "You are LegalHub's assistant: provide concise, accurate legal information, "
            "explain legal terms in plain language, and when unsure, state that you are not a lawyer."
        )
        
        prompt_parts = [f"System: {system}"]
        if context:
            prompt_parts.append("Conversation so far:")
            prompt_parts.extend(context)
        prompt_parts.append(f"User: {user_message}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)


# Global RAG service instance
rag_service = RAGService()
