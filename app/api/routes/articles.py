"""Articles API routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, timezone
from typing import Optional
import re

from app.dependencies import get_current_user, get_optional_user
from app.services.firebase_service import firebase_service
from app.models.article import firestore_article_to_model, article_model_to_firestore
from app.schemas.article import (
    ArticleCreateSchema,
    ArticleUpdateSchema,
    ArticleResponse,
    ArticleListResponse,
)
from app.models.user import UserRole


router = APIRouter(prefix="/api/v1/articles", tags=["Articles"])


def _slugify(text: str) -> str:
    """Create a URL-safe slug from a title"""
    s = (text or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "article"


def _generate_unique_slug(coll, title: str) -> str:
    base = _slugify(title)
    slug = base
    idx = 1
    existing = {doc.to_dict().get("slug") for doc in coll.stream()}
    while slug in existing:
        idx += 1
        slug = f"{base}-{idx}"
    return slug


@router.get("/", response_model=ArticleListResponse)
async def list_articles(
    q: Optional[str] = Query(None),
    page: int = 1,
    pageSize: int = 20,
    current_user=Depends(get_optional_user),
):
    """List articles with pagination"""
    filters = {}

    # Text search support (Simple)
    # Note: If 'q' is provided, we might fail if dataset is large because Firestore doesn't do "contains".
    # For now, we ignore 'q' in database query and just list recent articles.
    # Real solution requires Algolia/Elasticsearch or generic partial scan (slow).

    # Only show published articles by default
    filters["published"] = True

    # If admin or author, logic to see unpublished is complex to do in one query with filters.
    # We will prioritize the main use case: Public Feed.
    # Users/Authors seeing their own unpublished articles should be a separate endpoint "/my".

    docs, total_count = await firebase_service.query_collection(
        "articles",
        filters=filters,
        limit=pageSize,
        offset=(page - 1) * pageSize
    )

    items = []
    for doc_id, doc_data in docs:
        try:
            # Basic client-side filter for 'q' if provided (only filters the page, imperfect but safe)
            if q:
                text = (doc_data.get("title", "") + " " +
                        doc_data.get("content", "")).lower()
                if q.lower() not in text:
                    continue

            items.append(firestore_article_to_model(doc_data, doc_id))
        except Exception:
            continue

    # Calculate pages
    # Note: total_count from query_collection might be limited or estimated in some implementatons,
    # but our service does a separate count query.

    return ArticleListResponse(
        articles=[
            ArticleResponse.model_validate(a)
            for a in items
        ],
        total=total_count,
        page=page,
        page_size=pageSize,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str, current_user=Depends(get_optional_user)):
    coll = firebase_service.db.collection("articles")
    doc = coll.document(article_id).get()
    a = None
    if not doc.exists:
        # try lookup by slug by scanning collection (works with DummyDB in tests)
        found = None
        for d in coll.stream():
            if d.to_dict().get("slug") == article_id:
                found = d
                break
        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
            )
        a = firestore_article_to_model(found.to_dict(), found.id)
    else:
        a = firestore_article_to_model(doc.to_dict(), doc.id)
    # if not published, only author or admin can view
    if not a.published:
        if a.author_id != current_user.uid and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to view unpublished article",
            )
    return ArticleResponse.model_validate(a)


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: ArticleCreateSchema, current_user=Depends(get_current_user)
):
    uid = current_user.uid

    # allow lawyers, organizations (and admin) to create articles
    if current_user.role not in {UserRole.LAWYER, UserRole.ORGANIZATION, UserRole.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professionals can publish articles.",
        )

    coll = firebase_service.db.collection("articles")
    doc_ref = coll.document()
    now = datetime.now(timezone.utc)
    article_data = {
        "title": payload.title,
        "slug": _generate_unique_slug(coll, payload.title),
        "content": payload.content,
        "authorId": uid,
        "tags": payload.tags,
        "published": payload.published,
        "createdAt": now,
        "updatedAt": now,
        "likesCount": 0,
        "views": 0,
        "sharesCount": 0,
    }
    doc_ref.set(article_data)
    a = firestore_article_to_model(article_data, doc_ref.id)

    return ArticleResponse.model_validate(a)


@router.post("/{article_id}/like", response_model=dict)
async def toggle_like(article_id: str, current_user=Depends(get_current_user)):
    # store likes as subcollection articles/{id}/likes/{uid}
    uid = current_user.uid
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    likes_coll = (
        firebase_service.db.collection("articles")
        .document(article_id)
        .collection("likes")
    )
    like_ref = likes_coll.document(uid)
    existing = like_ref.get()
    if existing.exists:
        # remove like
        like_ref.delete()
        liked = False
    else:
        like_ref.set({"userId": uid, "createdAt": datetime.now(timezone.utc)})
        liked = True

    # compute total likes
    count = 0
    for _ in likes_coll.stream():
        count += 1

    # optionally update article document's likesCount
    try:
        firebase_service.db.collection("articles").document(article_id).update(
            {"likesCount": count}
        )
    except Exception:
        pass

    return {"liked": liked, "totalLikes": count}


@router.post("/{article_id}/share", response_model=dict)
async def share_article(
    article_id: str,
    payload: dict | None = None,
    current_user=Depends(get_optional_user),
):
    # allow anonymous shares; record user if available
    platform = None
    if payload and isinstance(payload, dict):
        platform = payload.get("platform")

    # create a share record under articles/{id}/shares
    shares_coll = (
        firebase_service.db.collection("articles")
        .document(article_id)
        .collection("shares")
    )
    # use user uid if present otherwise auto id
    uid = None
    if current_user:
        uid = current_user.uid

    if uid:
        ref = shares_coll.document(uid)
        ref.set(
            {
                "userId": uid,
                "platform": platform,
                "createdAt": datetime.now(timezone.utc),
            }
        )
    else:
        ref = shares_coll.document()
        ref.set({"platform": platform, "createdAt": datetime.now(timezone.utc)})

    # recompute count
    count = 0
    for _ in shares_coll.stream():
        count += 1

    try:
        firebase_service.db.collection("articles").document(article_id).update(
            {"sharesCount": count}
        )
    except Exception:
        pass

    # generate a simple share URL using slug when available
    coll = firebase_service.db.collection("articles")
    art_doc = coll.document(article_id).get()
    share_url = f"/api/articles/{article_id}"
    if art_doc.exists:
        art = art_doc.to_dict()
        if art.get("slug"):
            share_url = f"/api/articles/{art.get('slug')}"
    return {"shared": True, "totalShares": count, "shareUrl": share_url}


@router.post("/{article_id}/save", response_model=dict)
async def toggle_save(article_id: str, current_user=Depends(get_current_user)):
    uid = current_user.uid
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    # save as users/{uid}/bookmarks/{article_id}
    existing = await firebase_service.get_bookmark(uid, article_id)
    if existing:
        # remove bookmark
        await firebase_service.remove_bookmark(uid, article_id)
        saved = False
    else:
        # add bookmark
        await firebase_service.add_bookmark(uid, article_id)
        saved = True
    return {"saved": saved}


@router.post(
    "/{article_id}/comments", response_model=dict, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    article_id: str, payload: dict, current_user=Depends(get_current_user)
):
    # payload expected to include 'content'
    content = payload.get("content")
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Content required"
        )
    uid = current_user.uid
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    comments_coll = (
        firebase_service.db.collection("articles")
        .document(article_id)
        .collection("comments")
    )
    doc_ref = comments_coll.document()
    now = datetime.now(timezone.utc)
    data = {
        "articleId": article_id,
        "authorId": uid,
        "content": content,
        "createdAt": now,
    }
    doc_ref.set(data)
    return {
        "commentId": doc_ref.id,
        "articleId": article_id,
        "authorId": uid,
        "content": content,
        "createdAt": now,
    }


@router.get("/{article_id}/comments", response_model=list)
async def list_comments(article_id: str, page: int = 1, pageSize: int = 50):
    comments_coll = (
        firebase_service.db.collection("articles")
        .document(article_id)
        .collection("comments")
    )
    docs = list(comments_coll.stream())
    # sort by createdAt
    docs.sort(key=lambda d: d.to_dict().get("createdAt") or datetime.min)
    start = (page - 1) * pageSize
    page_docs = docs[start: start + pageSize]
    out = []
    for doc in page_docs:
        d = doc.to_dict()
        out.append(
            {
                "commentId": doc.id,
                "articleId": article_id,
                "authorId": d.get("authorId"),
                "content": d.get("content"),
                "createdAt": d.get("createdAt"),
            }
        )
    return out


@router.delete("/{article_id}/comments/{comment_id}")
async def delete_comment(
    article_id: str, comment_id: str, current_user=Depends(get_current_user)
):
    comments_coll = (
        firebase_service.db.collection("articles")
        .document(article_id)
        .collection("comments")
    )
    ref = comments_coll.document(comment_id)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    d = doc.to_dict()
    uid = current_user.uid
    if d.get("authorId") != uid and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete comment",
        )
    ref.delete()
    return {"deleted": True}


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: str,
    payload: ArticleUpdateSchema,
    current_user=Depends(get_current_user),
):
    doc_ref = firebase_service.db.collection("articles").document(article_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )

    existing = doc.to_dict()
    # Authorization: only author or admin can update
    uid = current_user.uid
    if existing.get("authorId") and uid and existing.get("authorId") != uid:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to modify this article",
            )

    update_data = {}
    if payload.title is not None:
        update_data["title"] = payload.title
    if payload.content is not None:
        update_data["content"] = payload.content
    if payload.tags is not None:
        update_data["tags"] = payload.tags
    if payload.published is not None:
        update_data["published"] = payload.published
    update_data["updatedAt"] = datetime.now(timezone.utc)

    doc_ref.update(update_data)
    # merge existing for response
    new_doc = doc_ref.get()
    a = firestore_article_to_model(new_doc.to_dict(), new_doc.id)
    return ArticleResponse.model_validate(a)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: str, current_user=Depends(get_current_user)):
    doc_ref = firebase_service.db.collection("articles").document(article_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )

    existing = doc.to_dict()
    uid = current_user.uid
    if existing.get("authorId") and uid and existing.get("authorId") != uid:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to delete this article",
            )

    doc_ref.delete()
    return None
