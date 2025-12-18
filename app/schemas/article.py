"""
Article request/response schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ArticleCreateSchema(BaseModel):
    title: str = Field(..., max_length=300)
    content: str = Field(..., description="Article body")
    tags: list[str] = Field(default_factory=list)
    published: bool = Field(default=False)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "title": "How to file a small claims case",
                "content": "Step-by-step guide...",
                "tags": ["small-claims", "procedure"],
                "published": True,
            }
        }
    )


class ArticleUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    published: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class ArticleResponse(BaseModel):
    article_id: str = Field(..., alias="articleId")
    title: str
    slug: Optional[str] = None
    content: str
    author_id: str = Field(..., alias="authorId")
    tags: list[str]
    published: bool
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    likes_count: int = Field(0, alias="likesCount")
    views: int = 0
    shares_count: int = Field(0, alias="sharesCount")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class CommentCreateSchema(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    comment_id: str = Field(..., alias="commentId")
    article_id: str = Field(..., alias="articleId")
    author_id: str = Field(..., alias="authorId")
    content: str
    created_at: Optional[datetime] = Field(None, alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class LikeResponse(BaseModel):
    liked: bool
    total_likes: int = Field(..., alias="totalLikes")

    model_config = ConfigDict(populate_by_name=True)


class SaveResponse(BaseModel):
    saved: bool
