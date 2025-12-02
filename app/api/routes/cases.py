"""
Case Management Routes for LegalHub Backend

This module defines the HTTP endpoints for case management operations:
- Create new cases (anonymous and identified)
- Retrieve case details
- List cases with filtering and pagination
- Update case information
- Manage case status and assignments
- Upload evidence/attachments
- Fetch case statistics
"""

import logging
from typing import Optional
from uuid import uuid4
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File

from app.dependencies import get_current_user
from app.services import firebase_service
from app.services.notification_service import notification_service
from app.services.ingestion_service import (
    ingestion_service,
)  # Import the ingestion service
from app.models.case import (
    Case,
    CaseStatus,
    CaseAttachment,  # Re-import CaseAttachment
    firestore_case_to_model,
    case_model_to_firestore,
)
from app.schemas.case import (
    CaseCreateSchema,
    CaseUpdateSchema,
    CaseStatusUpdateSchema,
    CaseDetailSchema,
    CaseListSchema,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cases", tags=["cases"])


# POST /api/cases - Create a new case
@router.post("/", response_model=CaseDetailSchema, status_code=201)
async def create_case(
    case_data: CaseCreateSchema,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Create a new case (anonymous or identified)

    - For anonymous cases: email and contactName are required
    - For identified cases: current user is automatically linked
    """
    try:
        logger.info(
            f"Creating case: category={case_data.category}, "
            f"anonymous={case_data.isAnonymous}"
        )

        # Validate anonymous submission
        if case_data.isAnonymous:
            if not case_data.email or not case_data.contactName:
                raise HTTPException(
                    status_code=400,
                    detail="Email and contact name are required for anonymous submissions",
                )

        # Create case model
        case_id = f"case_{uuid4().hex[:12]}"
        new_case = Case(
            caseId=case_id,
            userId=(
                current_user.get("uid")
                if current_user and not case_data.isAnonymous
                else None
            ),
            isAnonymous=case_data.isAnonymous,
            category=case_data.category,
            title=case_data.title,
            description=case_data.description,
            location=case_data.location,
            email=(
                case_data.email
                if case_data.isAnonymous
                else current_user.get("email") if current_user else None
            ),
            phone=case_data.phone,
            contactName=case_data.contactName,
            tags=case_data.tags,
            priority=case_data.priority,
            legalBasis=case_data.legalBasis,
            status=CaseStatus.SUBMITTED,
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC),
        )

        # Convert to Firestore format and save
        firestore_data = case_model_to_firestore(new_case)
        await firebase_service.set_document(f"cases/{case_id}", firestore_data)

        logger.info(f"Case created successfully: {case_id}")
        return CaseDetailSchema(**new_case.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating case: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create case")


# GET /api/cases/{case_id} - Get case details
@router.get("/{case_id}", response_model=CaseDetailSchema)
async def get_case(
    case_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Retrieve detailed information about a specific case"""
    try:
        logger.info(f"Fetching case: {case_id}")

        doc_data = await firebase_service.get_document(f"cases/{case_id}")
        if not doc_data:
            raise HTTPException(status_code=404, detail="Case not found")

        # Convert to model
        case = firestore_case_to_model(doc_data, case_id)

        # Increment view count
        doc_data["viewCount"] = doc_data.get("viewCount", 0) + 1
        doc_data["updatedAt"] = datetime.now(UTC)
        await firebase_service.update_document(f"cases/{case_id}", doc_data)

        return CaseDetailSchema(**case.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve case")


# GET /api/cases - List cases with pagination and filtering
@router.get("", response_model=CaseListSchema)
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    List cases with optional filtering by category, status, or priority

    Pagination: page and page_size query parameters
    Filtering: optional category, status, priority filters
    """
    try:
        logger.info(
            f"Listing cases: page={page}, page_size={page_size}, category={category}, status={status}"
        )

        # Build query filters
        filters = {}
        if category:
            filters["category"] = category
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority

        # Query Firestore
        docs, total_count = await firebase_service.query_collection(
            "cases", filters=filters, limit=page_size, offset=(page - 1) * page_size
        )

        # Convert documents to Case models
        cases = []
        for doc_id, doc_data in docs:
            try:
                case = firestore_case_to_model(doc_data, doc_id)
                cases.append(CaseDetailSchema(**case.model_dump()))
            except Exception as e:
                logger.warning(f"Error converting case {doc_id}: {str(e)}")
                continue

        total_pages = (total_count + page_size - 1) // page_size

        return CaseListSchema(
            cases=cases,
            total=total_count,
            page=page,
            pageSize=page_size,
            pages=total_pages if hasattr(CaseListSchema, "pages") else None,
        )

    except Exception as e:
        logger.error(f"Error listing cases: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cases")


# GET /api/cases/user/{user_id} - Get cases by user
@router.get("/user/{user_id}", response_model=CaseListSchema)
async def get_user_cases(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Retrieve all cases filed by a specific user

    Only the user or admins can view their own cases
    """
    try:
        # Check authorization
        if (
            current_user
            and current_user.get("uid") != user_id
            and not current_user.get("is_admin")
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to view these cases"
            )

        logger.info(f"Fetching cases for user: {user_id}")

        # Query cases by userId
        docs, total_count = await firebase_service.query_collection(
            "cases",
            filters={"userId": user_id},
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        cases = []
        for doc_id, doc_data in docs:
            try:
                case = firestore_case_to_model(doc_data, doc_id)
                cases.append(CaseDetailSchema(**case.model_dump()))
            except Exception as e:
                logger.warning(f"Error converting case {doc_id}: {str(e)}")
                continue

        total_pages = (total_count + page_size - 1) // page_size

        return CaseListSchema(
            cases=cases,
            total=total_count,
            page=page,
            pageSize=page_size,
            pages=total_pages if hasattr(CaseListSchema, "pages") else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user cases for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user cases")


# PUT /api/cases/{case_id} - Update case information
@router.put("/{case_id}", response_model=CaseDetailSchema)
async def update_case(
    case_id: str,
    case_data: CaseUpdateSchema,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Update case details (title, description, tags, etc.)"""
    try:
        # Verify case exists and user has permission
        doc_data = await firebase_service.get_document(f"cases/{case_id}")
        if not doc_data:
            raise HTTPException(status_code=404, detail="Case not found")

        # Check authorization
        if doc_data.get("userId") != current_user.get("uid") if current_user else None:
            if not current_user or not current_user.get("is_admin"):
                raise HTTPException(
                    status_code=403, detail="Not authorized to update this case"
                )

        logger.info(f"Updating case: {case_id}")

        # Update allowed fields
        update_data = {}
        if case_data.category:
            update_data["category"] = case_data.category.value
        if case_data.title:
            update_data["title"] = case_data.title
        if case_data.description:
            update_data["description"] = case_data.description
        if case_data.location:
            update_data["location"] = case_data.location.model_dump()
        if case_data.tags:
            update_data["tags"] = case_data.tags
        if case_data.priority:
            update_data["priority"] = case_data.priority
        if case_data.legalBasis:
            update_data["legalBasis"] = case_data.legalBasis

        update_data["updatedAt"] = datetime.now(UTC)

        # Merge with existing data
        doc_data.update(update_data)
        await firebase_service.update_document(f"cases/{case_id}", update_data)

        case = firestore_case_to_model(doc_data, case_id)
        # Notify case owner and assigned party about status change (best-effort)
        try:
            owner = doc_data.get("userId")
            if owner:
                await notification_service.send_to_user(
                    owner,
                    title="Case status updated",
                    body=f"Your case {case_id} status is now {case.status}",
                    data={"caseId": case_id, "status": case.status},
                )
            assigned = doc_data.get("assignedTo")
            if assigned:
                await notification_service.send_to_user(
                    assigned,
                    title="Case assigned/updated",
                    body=f"Case {case_id} assigned or updated: {case.status}",
                    data={"caseId": case_id, "status": case.status},
                )
        except Exception:
            pass
        return CaseDetailSchema(**case.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update case")


# PUT /api/cases/{case_id}/status - Update case status
@router.put("/{case_id}/status", response_model=CaseDetailSchema)
async def update_case_status(
    case_id: str,
    status_data: CaseStatusUpdateSchema,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Update case status and optionally assign to a lawyer/admin

    Requires admin or assigned handler permissions
    """
    try:
        # Verify case exists
        doc_data = await firebase_service.get_document(f"cases/{case_id}")
        if not doc_data:
            raise HTTPException(status_code=404, detail="Case not found")

        # Check authorization (admin or assigned handler)
        if not current_user or not (
            current_user.get("is_admin")
            or current_user.get("uid") == doc_data.get("assignedTo")
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to update case status"
            )

        logger.info(f"Updating case status: {case_id} -> {status_data.status}")

        # Add to status history
        status_history = doc_data.get("statusHistory", [])
        status_history.append(
            {
                "status": status_data.status.value,
                "changedAt": datetime.now(UTC).isoformat(),
                "changedBy": current_user.get("uid"),
                "notes": status_data.notes,
            }
        )

        # Update document
        update_data = {
            "status": status_data.status.value,
            "statusHistory": status_history,
            "statusNotes": status_data.notes,
            "updatedAt": datetime.now(UTC),
        }

        # Handle resolution/closure
        if status_data.status in [CaseStatus.RESOLVED, CaseStatus.CLOSED]:
            update_data["resolvedAt"] = (
                datetime.now(UTC) if status_data.status == CaseStatus.RESOLVED else None
            )
            update_data["closedAt"] = (
                datetime.now(UTC) if status_data.status == CaseStatus.CLOSED else None
            )

        # Assign if specified
        if status_data.assignedTo:
            update_data["assignedTo"] = status_data.assignedTo
            update_data["assignedAt"] = datetime.now(UTC)

        doc_data.update(update_data)
        await firebase_service.update_document(f"cases/{case_id}", update_data)

        case = firestore_case_to_model(doc_data, case_id)
        return CaseDetailSchema(**case.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating case status {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update case status")


# POST /api/cases/{case_id}/attachments - Upload case attachment
@router.post("/{case_id}/attachments", status_code=201)
async def upload_attachment(
    case_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Upload evidence/attachment files to a case

    Supports PDF, images, and common document formats
    """
    try:
        # Verify case exists
        doc_data = await firebase_service.get_document(f"cases/{case_id}")
        if not doc_data:
            raise HTTPException(status_code=404, detail="Case not found")

        # Check authorization
        if doc_data.get("userId") != current_user.get("uid") if current_user else None:
            if not current_user or not current_user.get("is_admin"):
                raise HTTPException(
                    status_code=403, detail="Not authorized to upload to this case"
                )

        logger.info(f"Uploading attachment to case {case_id}: {file.filename}")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Create attachment record
        attachment_id = f"att_{uuid4().hex[:12]}"

        # Upload to Firebase Storage
        file_content = await file.read()
        storage_path = f"cases/{case_id}/{attachment_id}/{file.filename}"

        file_url = await firebase_service.upload_file(
            storage_path,
            file_content,
            content_type=file.content_type or "application/octet-stream",
        )

        # If the uploaded file is a PDF, ingest it into the vector store
        if file.content_type == "application/pdf":
            try:
                # Use attachment_id as document_id for ingestion
                ingested_chunk_ids = await ingestion_service.ingest_document(
                    content=file_content,
                    document_id=attachment_id,
                    document_type="pdf",
                    metadata={
                        "case_id": case_id,
                        "file_name": file.filename,
                        "file_type": file.content_type,
                        "uploaded_by": (
                            current_user.get("uid") if current_user else "anonymous"
                        ),
                        "description": description,
                    },
                )
                logger.info(
                    f"PDF attachment {attachment_id} ingested into ChromaDB. Chunks: {ingested_chunk_ids}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to ingest PDF attachment {attachment_id} into ChromaDB: {e}"
                )
                # Do not re-raise, allow file upload to proceed even if RAG ingestion fails

        # Create attachment object
        attachment = CaseAttachment(
            attachmentId=attachment_id,
            fileName=file.filename,
            fileUrl=file_url,
            fileType=file.content_type or "application/octet-stream",
            fileSize=len(file_content),
            uploadedAt=datetime.now(UTC),
            uploadedBy=current_user.get("uid") if current_user else None,
        )

        # Add to case attachments
        attachments = doc_data.get("attachments", [])
        attachments.append(attachment.model_dump())

        update_data = {"attachments": attachments, "updatedAt": datetime.now(UTC)}

        await firebase_service.update_document(f"cases/{case_id}", update_data)

        logger.info(f"Attachment uploaded successfully: {attachment_id}")

        return {
            "attachmentId": attachment_id,
            "fileName": file.filename,
            "fileSize": len(file_content),
            "uploadedAt": datetime.now(UTC).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading attachment to case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload attachment")


# GET /api/cases/stats - Get case statistics
@router.get("/stats/overview", status_code=200)
async def get_case_stats(
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Get aggregate case statistics (admin only)

    Returns counts by category, status, priority, and resolution metrics
    """
    try:
        if not current_user or not current_user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info("Fetching case statistics")

        # Get all cases for stats calculation
        docs, total_count = await firebase_service.query_collection(
            "cases", filters={}, limit=10000  # Large limit for stat aggregation
        )

        stats = {
            "totalCases": total_count,
            "totalAnonymousCases": 0,
            "totalIdentifiedCases": 0,
            "casesByCategory": {},
            "casesByStatus": {},
            "casesByPriority": {},
            "pendingCases": 0,
            "resolvedCases": 0,
            "averageResolutionTime": None,
            "casesByLocation": {},
            "lastUpdatedAt": datetime.now(UTC).isoformat(),
        }

        # Aggregate statistics
        resolution_times = []

        for doc_id, doc_data in docs:
            # Count anonymous/identified
            if doc_data.get("isAnonymous"):
                stats["totalAnonymousCases"] += 1
            else:
                stats["totalIdentifiedCases"] += 1

            # Count by category
            category = doc_data.get("category", "other")
            stats["casesByCategory"][category] = (
                stats["casesByCategory"].get(category, 0) + 1
            )

            # Count by status
            status = doc_data.get("status", "submitted")
            stats["casesByStatus"][status] = stats["casesByStatus"].get(status, 0) + 1

            # Count by priority
            priority = doc_data.get("priority", "medium")
            stats["casesByPriority"][priority] = (
                stats["casesByPriority"].get(priority, 0) + 1
            )

            # Count pending
            if status in ["submitted", "under_review", "in_progress"]:
                stats["pendingCases"] += 1

            # Count resolved
            if status == "resolved":
                stats["resolvedCases"] += 1
                if doc_data.get("resolvedAt") and doc_data.get("createdAt"):
                    resolution_time = (
                        doc_data["resolvedAt"] - doc_data["createdAt"]
                    ).days
                    resolution_times.append(resolution_time)

            # Count by location
            if doc_data.get("location"):
                location = doc_data["location"].get("country", "unknown")
                stats["casesByLocation"][location] = (
                    stats["casesByLocation"].get(location, 0) + 1
                )

        # Calculate average resolution time
        if resolution_times:
            stats["averageResolutionTime"] = sum(resolution_times) / len(
                resolution_times
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching case statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
