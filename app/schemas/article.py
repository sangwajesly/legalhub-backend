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
        json_schema_extra={
            "example": {
                "title": "How to file a small claims case",
                "content": "Step-by-step guide...",
                "tags": ["small-claims", "procedure"],
                "published": True
            }
        }
    )


class ArticleUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    published: Optional[bool] = None

    model_config = ConfigDict()


class ArticleResponse(BaseModel):
    articleId: str
    title: str
    slug: Optional[str] = None
    content: str
    authorId: str
    tags: list[str]
    published: bool
    createdAt: Optional[datetime]
    updatedAt: Optional[datetime]
    likesCount: int = 0
    views: int = 0
    sharesCount: int = 0

    model_config = ConfigDict()


class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    page: int
    pageSize: int

    model_config = ConfigDict()



class CommentCreateSchema(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    commentId: str
    articleId: str
    authorId: str
    content: str
    createdAt: Optional[datetime]


class LikeResponse(BaseModel):
    liked: bool
    totalLikes: int


class SaveResponse(BaseModel):
    saved: bool

