"""
Article model and Firestore conversion helpers
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Article(BaseModel):
    article_id: str
    title: str
    slug: Optional[str] = None
    content: str
    author_id: str
    tags: list[str] = Field(default_factory=list)
    published: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    likes_count: int = 0
    views: int = 0
    shares_count: int = 0

    model_config = ConfigDict()


def firestore_article_to_model(doc: dict, doc_id: str) -> Article:
    return Article(
        article_id=doc_id,
        title=doc.get("title"),
        slug=doc.get("slug"),
        content=doc.get("content"),
        author_id=doc.get("authorId") or doc.get("author_id"),
        tags=doc.get("tags", []),
        published=doc.get("published", False),
        created_at=doc.get("createdAt") or doc.get("created_at"),
        updated_at=doc.get("updatedAt") or doc.get("updated_at"),
        likes_count=doc.get("likesCount") or doc.get("likes_count") or 0,
        views=doc.get("views") or 0,
        shares_count=doc.get("sharesCount") or doc.get("shares_count") or 0,
    )


def article_model_to_firestore(article: Article) -> dict:
    return {
        "title": article.title,
        "slug": article.slug,
        "content": article.content,
        "authorId": article.author_id,
        "tags": article.tags,
        "published": article.published,
        "createdAt": article.created_at,
        "updatedAt": article.updated_at,
    }
