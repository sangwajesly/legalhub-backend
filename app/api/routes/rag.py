"""
RAG API endpoints for document ingestion and RAG-augmented chat
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import Optional, List
import os
import tempfile

from app.dependencies import get_current_user
from app.services.rag_service import rag_service
from app.services import langchain_service
from app.schemas.chat import MessageRequest, MessageResponse
from app.utils.rag_helpers import (
    add_article_to_rag,
    add_case_law_to_rag,
    add_statute_to_rag,
    batch_add_documents,
)

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


@router.post("/documents/add")
async def add_documents(
    documents: List[dict],
    current_user: dict = Depends(get_current_user),
):
    """
    Add documents to the RAG vector store.
    
    Each document should have:
    - id: unique identifier
    - content: document text
    - source: source of the document (e.g., "article", "case_law")
    """
    try:
        result = await rag_service.add_documents(documents)
        return {
            "status": "success",
            "added": result.get("added", 0),
            "skipped": result.get("skipped", 0),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding documents: {str(e)}",
        )


@router.post("/documents/upload")
async def upload_documents(
    file: UploadFile = File(...),
    source: str = "uploaded_file",
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a text file and add its content to the RAG vector store.
    
    Supported formats: .txt, .md
    """
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Read file content
            with open(tmp_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            # Create document
            document = {
                "id": file.filename,
                "content": text_content,
                "source": source,
            }

            # Add to RAG
            result = await rag_service.add_documents([document])

            return {
                "status": "success",
                "filename": file.filename,
                "added": result.get("added", 0),
                "message": f"Successfully added {file.filename} to RAG vector store",
            }
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}",
        )


@router.post("/search")
async def search_documents(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.3,
    current_user: dict = Depends(get_current_user),
):
    """
    Search the RAG vector store for relevant documents.
    
    Args:
        query: Search query
        top_k: Number of top results to return
        score_threshold: Minimum similarity score (0-1)
    """
    try:
        documents = await rag_service.retrieve_documents(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        return {
            "query": query,
            "count": len(documents),
            "documents": documents,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}",
        )


@router.post("/chat/message", response_model=MessageResponse)
async def send_rag_message(
    payload: MessageRequest,
    use_rag: bool = True,
    top_k: int = 3,
    current_user: dict = Depends(get_current_user),
):
    """
    Send a message with RAG augmentation.
    
    Args:
        payload: Message request with sessionId and message
        use_rag: Whether to use RAG enhancement (default: True)
        top_k: Number of top documents to retrieve
    """
    try:
        session_id = payload.sessionId or None
        
        # Generate RAG response
        reply, retrieved_docs = await langchain_service.generate_rag_response(
            session_id=session_id,
            user_id=current_user.get("uid"),
            user_message=payload.message,
            use_rag=use_rag,
            top_k=top_k,
        )

        return {
            "reply": reply,
            "sessionId": session_id or "",
            "retrieved_documents": retrieved_docs if use_rag else [],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}",
        )


@router.post("/chat/message/stream")
async def send_rag_message_stream(
    payload: MessageRequest,
    use_rag: bool = True,
    top_k: int = 3,
    current_user: dict = Depends(get_current_user),
):
    """
    Stream a RAG-augmented message response.
    
    Uses Server-Sent Events (SSE) for streaming.
    """
    from fastapi.responses import StreamingResponse

    session_id = payload.sessionId or None

    async def event_stream():
        try:
            # Yield initial comment
            yield ": stream open\n\n"
            
            # Stream RAG response
            async for chunk in langchain_service.generate_rag_response_stream(
                session_id=session_id,
                user_id=current_user.get("uid"),
                user_message=payload.message,
                use_rag=use_rag,
                top_k=top_k,
            ):
                if chunk is None:
                    continue
                # Format as SSE
                data = str(chunk).replace("\n", "\ndata: ")
                yield f"data: {data}\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/articles/add")
async def add_article_endpoint(
    article_id: str,
    title: str,
    content: str,
    author: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Add a legal article directly to the RAG vector store.
    
    Args:
        article_id: Unique article identifier
        title: Article title
        content: Full article content
        author: Optional author name
        category: Optional category (contract_law, criminal_law, etc.)
    """
    try:
        result = await add_article_to_rag(
            article_id=article_id,
            title=title,
            content=content,
            author=author,
            category=category,
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Article {article_id} added to RAG",
                "result": result,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to add article"),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding article: {str(e)}",
        )


@router.post("/cases/add")
async def add_case_endpoint(
    case_id: str,
    case_name: str,
    content: str,
    year: Optional[int] = None,
    jurisdiction: Optional[str] = None,
    case_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Add case law/court decision to the RAG vector store.
    
    Args:
        case_id: Unique case identifier
        case_name: Name of the case
        content: Full case text/decision
        year: Year of decision
        jurisdiction: Court jurisdiction
        case_type: Type of case (criminal, civil, etc.)
    """
    try:
        result = await add_case_law_to_rag(
            case_id=case_id,
            case_name=case_name,
            content=content,
            year=year,
            jurisdiction=jurisdiction,
            case_type=case_type,
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Case {case_id} added to RAG",
                "result": result,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to add case"),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding case: {str(e)}",
        )


@router.post("/statutes/add")
async def add_statute_endpoint(
    statute_id: str,
    statute_name: str,
    content: str,
    jurisdiction: Optional[str] = None,
    section: Optional[str] = None,
    effective_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Add a statute/law to the RAG vector store.
    
    Args:
        statute_id: Unique statute identifier
        statute_name: Name of the statute
        content: Full statute text
        jurisdiction: Jurisdiction
        section: Section number
        effective_date: When effective
    """
    try:
        result = await add_statute_to_rag(
            statute_id=statute_id,
            statute_name=statute_name,
            content=content,
            jurisdiction=jurisdiction,
            section=section,
            effective_date=effective_date,
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Statute {statute_id} added to RAG",
                "result": result,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to add statute"),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding statute: {str(e)}",
        )
