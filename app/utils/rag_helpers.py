"""
Helper utilities for RAG document ingestion and management.

This module provides convenient functions to:
- Add documents from various sources (articles, cases, PDFs)
- Batch ingest documents efficiently
- Format documents for embedding and storage
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, UTC

from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


async def add_article_to_rag(
    article_id: str,
    title: str,
    content: str,
    author: Optional[str] = None,
    category: Optional[str] = None,
    url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add a legal article to the RAG vector store.
    
    Args:
        article_id: Unique identifier for the article
        title: Article title
        content: Full article content/text
        author: Optional article author
        category: Optional article category (e.g., "criminal_law", "civil_law")
        url: Optional URL to the original article
        
    Returns:
        Dict with ingestion result
    """
    try:
        # Format the document with title and content
        formatted_content = f"Title: {title}\n\n{content}"
        
        document = {
            "id": f"article_{article_id}",
            "content": formatted_content,
            "source": "legal_article",
        }
        
        metadata = {
            "article_id": article_id,
            "title": title,
            "author": author or "unknown",
            "category": category or "general",
            "url": url or "",
            "added_at": datetime.now(UTC).isoformat(),
        }
        
        result = await rag_service.add_documents([document], metadata)
        logger.info(f"Added article {article_id} to RAG: {result}")
        return {
            "status": "success",
            "article_id": article_id,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error adding article to RAG: {e}")
        return {
            "status": "error",
            "article_id": article_id,
            "error": str(e),
        }


async def add_case_law_to_rag(
    case_id: str,
    case_name: str,
    content: str,
    year: Optional[int] = None,
    jurisdiction: Optional[str] = None,
    case_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add case law/court decision to the RAG vector store.
    
    Args:
        case_id: Unique case identifier
        case_name: Name of the case
        content: Full case text/decision
        year: Year of the decision
        jurisdiction: Jurisdiction (e.g., "Federal Court", "Supreme Court")
        case_type: Type of case (e.g., "criminal", "civil", "constitutional")
        
    Returns:
        Dict with ingestion result
    """
    try:
        formatted_content = f"Case: {case_name}\n\n{content}"
        
        document = {
            "id": f"case_{case_id}",
            "content": formatted_content,
            "source": "case_law",
        }
        
        metadata = {
            "case_id": case_id,
            "case_name": case_name,
            "year": year or datetime.now(UTC).year,
            "jurisdiction": jurisdiction or "unknown",
            "case_type": case_type or "general",
            "added_at": datetime.now(UTC).isoformat(),
        }
        
        result = await rag_service.add_documents([document], metadata)
        logger.info(f"Added case {case_id} to RAG: {result}")
        return {
            "status": "success",
            "case_id": case_id,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error adding case law to RAG: {e}")
        return {
            "status": "error",
            "case_id": case_id,
            "error": str(e),
        }


async def add_statute_to_rag(
    statute_id: str,
    statute_name: str,
    content: str,
    jurisdiction: Optional[str] = None,
    section: Optional[str] = None,
    effective_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add a statute/law to the RAG vector store.
    
    Args:
        statute_id: Unique statute identifier
        statute_name: Name of the statute
        content: Full statute text
        jurisdiction: Jurisdiction (e.g., "Federal", "State Name")
        section: Section number/reference
        effective_date: When the statute became effective
        
    Returns:
        Dict with ingestion result
    """
    try:
        formatted_content = f"Statute: {statute_name}\nSection: {section or 'N/A'}\n\n{content}"
        
        document = {
            "id": f"statute_{statute_id}",
            "content": formatted_content,
            "source": "statute",
        }
        
        metadata = {
            "statute_id": statute_id,
            "statute_name": statute_name,
            "jurisdiction": jurisdiction or "unknown",
            "section": section or "N/A",
            "effective_date": effective_date or "",
            "added_at": datetime.now(UTC).isoformat(),
        }
        
        result = await rag_service.add_documents([document], metadata)
        logger.info(f"Added statute {statute_id} to RAG: {result}")
        return {
            "status": "success",
            "statute_id": statute_id,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error adding statute to RAG: {e}")
        return {
            "status": "error",
            "statute_id": statute_id,
            "error": str(e),
        }


async def batch_add_documents(
    documents: List[Dict[str, Any]],
    source_type: str = "document",
) -> Dict[str, Any]:
    """
    Batch add multiple documents to the RAG vector store.
    
    Args:
        documents: List of document dicts with 'id', 'content', and optional metadata
        source_type: Type of source ("article", "case_law", "statute", "document")
        
    Returns:
        Dict with batch ingestion results
    """
    try:
        processed_docs = []
        
        for doc in documents:
            processed_doc = {
                "id": doc.get("id", f"doc_{len(processed_docs)}"),
                "content": doc.get("content", ""),
                "source": source_type,
            }
            
            if processed_doc["content"]:
                processed_docs.append(processed_doc)
        
        if not processed_docs:
            return {
                "status": "error",
                "error": "No valid documents to process",
            }
        
        result = await rag_service.add_documents(processed_docs)
        logger.info(f"Batch added {result.get('added', 0)} documents to RAG")
        return {
            "status": "success",
            "added": result.get("added", 0),
            "skipped": result.get("skipped", 0),
        }
    except Exception as e:
        logger.error(f"Error in batch add documents: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


async def ingest_from_firebase_articles() -> Dict[str, Any]:
    """
    Ingest all published articles from Firebase into RAG.
    
    This utility function fetches articles from Firestore and adds them to the RAG system.
    
    Returns:
        Dict with ingestion statistics
    """
    try:
        from app.services import firebase_service
        
        # Fetch all articles from Firebase
        articles = await firebase_service.get_all_articles()
        
        if not articles:
            return {
                "status": "success",
                "message": "No articles found in Firebase",
                "ingested": 0,
            }
        
        # Prepare documents for RAG
        documents = []
        for article in articles:
            doc = {
                "id": f"article_{article.uid}",
                "content": f"Title: {article.title}\n\nAuthor: {article.author_id}\n\n{article.content}",
                "source": "firebase_articles",
            }
            documents.append(doc)
        
        # Batch add to RAG
        result = await batch_add_documents(documents, "article")
        
        return {
            "status": "success",
            "total_articles": len(articles),
            "ingested": result.get("added", 0),
            "skipped": result.get("skipped", 0),
        }
    except Exception as e:
        logger.error(f"Error ingesting articles from Firebase: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


async def search_rag(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.3,
) -> Dict[str, Any]:
    """
    Search the RAG vector store for relevant documents.
    
    Args:
        query: Search query
        top_k: Number of results to return
        score_threshold: Minimum relevance score (0-1)
        
    Returns:
        Dict with search results
    """
    try:
        documents = await rag_service.retrieve_documents(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        
        return {
            "status": "success",
            "query": query,
            "results_count": len(documents),
            "documents": documents,
        }
    except Exception as e:
        logger.error(f"Error searching RAG: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


# Example usage functions

async def example_add_single_article():
    """Example: Add a single article to RAG"""
    result = await add_article_to_rag(
        article_id="article_001",
        title="Understanding Contract Law Basics",
        content="""
        Contracts are agreements between two or more parties that create legal obligations.
        For a contract to be valid, it must have:
        1. Offer and acceptance
        2. Consideration (exchange of value)
        3. Intention to create legal relations
        4. Capacity of parties
        5. Legality of purpose
        
        There are various types of contracts including:
        - Fixed-price contracts
        - Time and materials contracts
        - Cost-plus contracts
        """,
        author="Legal Expert",
        category="contract_law",
    )
    return result


async def example_add_multiple_documents():
    """Example: Add multiple documents in batch"""
    documents = [
        {
            "id": "statute_001",
            "content": "The Contract Act, 1872 governs contracts in India...",
        },
        {
            "id": "case_001",
            "content": "In the landmark case of ABC v XYZ, the court ruled...",
        },
        {
            "id": "article_001",
            "content": "Understanding the principles of tort law and liability...",
        },
    ]
    
    result = await batch_add_documents(documents, source_type="document")
    return result


async def example_search():
    """Example: Search for documents"""
    result = await search_rag(
        query="What are the requirements for a valid contract?",
        top_k=5,
    )
    return result


if __name__ == "__main__":
    # Run examples
    import asyncio
    
    async def main():
        print("Example 1: Add single article")
        result1 = await example_add_single_article()
        print(result1)
        
        print("\nExample 2: Add multiple documents")
        result2 = await example_add_multiple_documents()
        print(result2)
        
        print("\nExample 3: Search documents")
        result3 = await example_search()
        print(result3)
    
    asyncio.run(main())
