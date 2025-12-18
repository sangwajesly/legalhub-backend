"""
Article model and Firestore conversion helpers
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Article(BaseModel):
    article_id: str = Field(..., alias="articleId")
    title: str
    slug: Optional[str] = None
    content: str
    author_id: str = Field(..., alias="authorId")
    tags: list[str] = Field(default_factory=list)
    published: bool = False
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    likes_count: int = Field(0, alias="likesCount")
    views: int = 0
    shares_count: int = Field(0, alias="sharesCount")

    model_config = ConfigDict(populate_by_name=True)


def firestore_article_to_model(doc: dict, doc_id: str) -> Article:
    return Article.model_validate({**doc, "articleId": doc_id})


def article_model_to_firestore(article: Article) -> dict:
    data = article.model_dump(by_alias=True)
    data.pop("articleId", None)
    return data
