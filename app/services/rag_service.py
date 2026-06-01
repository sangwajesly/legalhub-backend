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
from app.services import ai_service, firebase_service
from app.utils.vector_store import get_vector_store

from app.models.chat import ChatMessage
from app.prompts import (
    RAG_SYSTEM_PROMPT_TEMPLATE,
    LEGALHUB_CORE_SYSTEM_PROMPT,
    LEGALHUB_NO_DOCS_SYSTEM_PROMPT,
    QUERY_EXPANSION_PROMPT,
)

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
            logger.info(
                f"RAG collection '{self.collection_name}' initialized with FAISS")
            print(
                f"[OK] FAISS vector store initialized: {self.vector_store.count()} documents")
        except Exception as e:
            logger.error(f"Failed to initialize RAG collection: {e}")
            raise

    async def _expand_query(self, user_query: str) -> str:
        """
        Rewrite a conversational query into precise Cameroonian legal terminology
        before FAISS retrieval. Returns "off-topic query" for clearly unrelated input.
        Falls back to the original query on any error.
        """
        try:
            prompt = QUERY_EXPANSION_PROMPT.format(user_query=user_query)
            result = await ai_service.send_message(prompt)
            expanded = result.get("response", "").strip() if isinstance(result, dict) else str(result).strip()
            if expanded and len(expanded) > 3:
                logger.info(f"Query expanded: '{user_query[:40]}' -> '{expanded[:60]}'")
                return expanded
        except Exception as e:
            logger.warning(f"Query expansion failed (using original): {e}")
        return user_query

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
            # Merge global metadata into each document if provided
            if metadata:
                for doc in documents:
                    if "metadata" not in doc:
                        doc["metadata"] = {}
                    doc["metadata"].update(metadata)

            # FAISS add_documents is synchronous, run in thread pool
            result = await asyncio.to_thread(
                self.vector_store.add_documents,
                documents
            )
            logger.info(
                f"Added {result.get('added', 0)} documents to FAISS vector store")
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
            documents = [doc for doc in results if doc.get(
                'score', 0) >= score_threshold]

            logger.info(
                f"Retrieved {len(documents)} documents for query: {query[:50]}...")
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
            # Source and page can be in doc directly or in metadata
            source = doc.get("source") or doc.get(
                "metadata", {}).get("source", "unknown")
            page = doc.get("page") or doc.get(
                "metadata", {}).get("page")

            # Format context chunk with page details for precise LLM legal citations
            if page:
                chunk = f"[Source: {source}, Page: {page} (relevance: {score:.2f})]\n{content}\n"
            else:
                chunk = f"[Source: {source} (relevance: {score:.2f})]\n{content}\n"
            
            chunk_length = len(chunk)

            if total_length + chunk_length > max_context_length:
                break

            context_parts.append(chunk)
            total_length += chunk_length

        # Construct augmented prompt
        context = "\n".join(context_parts)
        return RAG_SYSTEM_PROMPT_TEMPLATE.format(
            context=context,
            user_query=user_query
        )

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

        Returns:
            Tuple of (response_text, retrieved_documents)
        """
        retrieved_docs = []

        try:
            # 1. Persist user message
            if session_id:
                await firebase_service.add_chat_message(session_id, ChatMessage(
                    role="user", text=user_message,
                    userId=user_id, createdAt=datetime.now(UTC)
                ))

            # 2. Expand query; detect off-topic early
            search_query = user_message
            if use_rag:
                search_query = await self._expand_query(user_message)

                # Short-circuit: query expander flagged this as off-topic
                if search_query.strip().lower() == "off-topic query":
                    logger.info("Off-topic query detected — skipping FAISS, using no-docs prompt.")
                    final_prompt = await self._build_chat_context_prompt(
                        session_id, user_message, no_docs_found=True
                    )
                    ai_result = await ai_service.send_message(final_prompt)
                    reply = ai_result.get("response", str(ai_result)) if isinstance(ai_result, dict) else str(ai_result)
                    if session_id:
                        await firebase_service.add_chat_message(session_id, ChatMessage(
                            role="assistant", text=reply,
                            userId=user_id, createdAt=datetime.now(UTC)
                        ))
                    return reply, []

                retrieved_docs = await self.retrieve_documents(search_query, top_k=top_k)

            # 3. Build prompt
            if retrieved_docs and use_rag:
                final_prompt = await self.augment_prompt(user_message, retrieved_docs)
            else:
                # No docs found — use dedicated no-docs prompt
                final_prompt = await self._build_chat_context_prompt(
                    session_id, user_message,
                    no_docs_found=use_rag  # True only if we tried RAG but found nothing
                )

            # 4. Generate response
            try:
                ai_result = await ai_service.send_message(final_prompt)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return "I'm sorry, I couldn't process that right now. Please try again later.", retrieved_docs

            # 5. Normalize
            reply = ai_result.get("response", str(ai_result)) if isinstance(ai_result, dict) else str(ai_result)
            if not reply:
                reply = ""

            # 6. Persist assistant message
            if session_id:
                await firebase_service.add_chat_message(session_id, ChatMessage(
                    role="assistant", text=reply,
                    userId=user_id, createdAt=datetime.now(UTC)
                ))

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
                await firebase_service.add_chat_message(session_id, ChatMessage(
                    role="user", text=user_message,
                    userId=user_id, createdAt=datetime.now(UTC)
                ))

            # 2. Expand query; detect off-topic early
            search_query = user_message
            if use_rag:
                search_query = await self._expand_query(user_message)

                if search_query.strip().lower() == "off-topic query":
                    logger.info("Off-topic query detected (stream) — skipping FAISS.")
                    final_prompt = await self._build_chat_context_prompt(
                        session_id, user_message, no_docs_found=True
                    )
                    final_parts = []
                    async for chunk in ai_service.stream_send_message(final_prompt):
                        text = chunk.get("response", "") if isinstance(chunk, dict) else str(chunk)
                        final_parts.append(text)
                        yield text
                    if session_id:
                        await firebase_service.add_chat_message(session_id, ChatMessage(
                            role="assistant", text="".join(final_parts),
                            userId=user_id, createdAt=datetime.now(UTC)
                        ))
                    return

                retrieved_docs = await self.retrieve_documents(search_query, top_k=top_k)

            # 3. Build prompt
            if retrieved_docs and use_rag:
                final_prompt = await self.augment_prompt(user_message, retrieved_docs)
            else:
                final_prompt = await self._build_chat_context_prompt(
                    session_id, user_message,
                    no_docs_found=use_rag
                )

            # 4. Stream response from LLM
            final_parts = []
            try:
                async for chunk in ai_service.stream_send_message(final_prompt):
                    text = chunk.get("response", "") if isinstance(
                        chunk, dict) else str(chunk)
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
        max_messages: int = 5,
        max_prompt_length: int = 4000,
        no_docs_found: bool = False
    ) -> str:
        """
        Build a prompt using chat history context.
        Uses LEGALHUB_NO_DOCS_SYSTEM_PROMPT when RAG retrieval returned nothing,
        so the model handles off-topic and knowledge-gap questions correctly.
        """
        context_messages = []

        if session_id:
            try:
                msgs = await firebase_service.get_chat_history(session_id)
                if msgs:
                    msgs = [m for m in msgs if m]
                    context_messages = [f"{m.role}: {m.text}" for m in msgs]
            except Exception as e:
                logger.warning(f"Failed to load chat history: {e}")

        # Choose system prompt based on whether docs were found
        system = LEGALHUB_NO_DOCS_SYSTEM_PROMPT if no_docs_found else LEGALHUB_CORE_SYSTEM_PROMPT

        prompt_parts = [f"System: {system}"]
        base_prompt_length = len("\n".join(prompt_parts)) + \
            len(f"\nUser: {user_message}\nAssistant:")

        if context_messages:
            current_history_length = 0
            temp_history_parts = []
            for msg_text in reversed(context_messages):
                if base_prompt_length + current_history_length + len(msg_text) + len("\nConversation so far:") > max_prompt_length:
                    logger.warning(f"Truncating chat history for session {session_id}.")
                    break
                temp_history_parts.insert(0, msg_text)
                current_history_length += len(msg_text) + 1

            if temp_history_parts:
                prompt_parts.append("Conversation so far:")
                prompt_parts.extend(temp_history_parts)

        prompt_parts.append(f"User: {user_message}")
        prompt_parts.append("Assistant:")

        return "\n".join(prompt_parts)


# Global RAG service instance
rag_service = RAGService()
