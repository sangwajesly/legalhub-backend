"""Articles API routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, timezone
from typing import Optional

from app.dependencies import get_current_user, get_optional_user
from app.services.firebase_service import firebase_service
from app.models.article import firestore_article_to_model, article_model_to_firestore
from app.schemas.article import (
	ArticleCreateSchema,
	ArticleUpdateSchema,
	ArticleResponse,
	ArticleListResponse,
)


router = APIRouter(prefix="/api/articles", tags=["Articles"])


@router.get("/", response_model=ArticleListResponse)
async def list_articles(q: Optional[str] = Query(None), page: int = 1, pageSize: int = 20, current_user=Depends(get_optional_user)):
	"""List articles with optional simple query and pagination"""
	# Simple implementation: fetch all and filter in-memory for small datasets/tests
	coll = firebase_service.db.collection("articles")
	docs = coll.stream()

	items = []
	for doc in docs:
		data = doc.to_dict()
		is_published = data.get("published", False)
		# include published always; include unpublished when the current_user is the author or admin
		include = False
		if is_published:
			include = True
		else:
			if current_user:
				uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("sub") if isinstance(current_user, dict) else None)
				role = getattr(current_user, "role", None) or (current_user.get("role") if isinstance(current_user, dict) else None)
				if uid and data.get("authorId") == uid:
					include = True
				if role == "admin":
					include = True
		if not include:
			continue
		if q:
			if q.lower() not in (data.get("title", "").lower() + data.get("content", "").lower()):
				continue
		items.append(firestore_article_to_model(data, doc.id))

	# sort by createdAt desc if available
	items.sort(key=lambda x: x.created_at or datetime.min, reverse=True)

	total = len(items)
	start = (page - 1) * pageSize
	end = start + pageSize
	page_items = items[start:end]

	return ArticleListResponse(
		articles=[ArticleResponse(
			articleId=a.article_id,
			title=a.title,
			slug=a.slug,
			content=a.content,
			authorId=a.author_id,
			tags=a.tags,
			published=a.published,
			createdAt=a.created_at,
			updatedAt=a.updated_at,
			likesCount=a.likes_count,
			views=a.views,
		) for a in page_items],
		total=total,
		page=page,
		pageSize=pageSize,
	)


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str, current_user=Depends(get_optional_user)):
	doc = firebase_service.db.collection("articles").document(article_id).get()
	if not doc.exists:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
	a = firestore_article_to_model(doc.to_dict(), doc.id)
	# if not published, only author or admin can view
	if not a.published:
		uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) if current_user else None
		role = getattr(current_user, "role", None) or (current_user.get("role") if isinstance(current_user, dict) else None) if current_user else None
		if a.author_id != uid and role != "admin":
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view unpublished article")
	return ArticleResponse(
		articleId=a.article_id,
		title=a.title,
		slug=a.slug,
		content=a.content,
		authorId=a.author_id,
		tags=a.tags,
		published=a.published,
		createdAt=a.created_at,
		updatedAt=a.updated_at,
		likesCount=a.likes_count,
		views=a.views,
	)


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(payload: ArticleCreateSchema, current_user=Depends(get_current_user)):
	# current_user may be a dict (firebase token) or User model; try to extract uid
	uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("user_id") if isinstance(current_user, dict) else None)
	if not uid:
		# fallback: some tokens use 'sub'
		uid = current_user.get("sub") if isinstance(current_user, dict) else None
	if not uid:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

	# allow users, lawyers and organizations (and admin) to create articles
	role = getattr(current_user, "role", None) or (current_user.get("role") if isinstance(current_user, dict) else None)
	allowed_roles = {"user", "lawyer", "organization", "admin"}
	if role not in allowed_roles:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role to create articles")

	doc_ref = firebase_service.db.collection("articles").document()
	now = datetime.now(timezone.utc)
	article_data = {
		"title": payload.title,
		"slug": None,
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

	return ArticleResponse(
		articleId=a.article_id,
		title=a.title,
		slug=a.slug,
		content=a.content,
		authorId=a.author_id,
		tags=a.tags,
		published=a.published,
		createdAt=a.created_at,
		updatedAt=a.updated_at,
		likesCount=a.likes_count,
		views=a.views,
		sharesCount=a.shares_count,
	)


@router.post("/{article_id}/like", response_model=dict)
async def toggle_like(article_id: str, current_user=Depends(get_current_user)):
	# store likes as subcollection articles/{id}/likes/{uid}
	uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("sub") if isinstance(current_user, dict) else None)
	if not uid:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

	likes_coll = firebase_service.db.collection("articles").document(article_id).collection("likes")
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
		firebase_service.db.collection("articles").document(article_id).update({"likesCount": count})
	except Exception:
		pass

	return {"liked": liked, "totalLikes": count}


@router.post("/{article_id}/share", response_model=dict)
async def share_article(article_id: str, payload: dict | None = None, current_user=Depends(get_optional_user)):
	# allow anonymous shares; record user if available
	platform = None
	if payload and isinstance(payload, dict):
		platform = payload.get("platform")

	# create a share record under articles/{id}/shares
	shares_coll = firebase_service.db.collection("articles").document(article_id).collection("shares")
	# use user uid if present otherwise auto id
	uid = None
	if current_user:
		uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("sub") if isinstance(current_user, dict) else None)

	if uid:
		ref = shares_coll.document(uid)
		ref.set({"userId": uid, "platform": platform, "createdAt": datetime.now(timezone.utc)})
	else:
		ref = shares_coll.document()
		ref.set({"platform": platform, "createdAt": datetime.now(timezone.utc)})

	# recompute count
	count = 0
	for _ in shares_coll.stream():
		count += 1

	try:
		firebase_service.db.collection("articles").document(article_id).update({"sharesCount": count})
	except Exception:
		pass

	# generate a simple share URL using article id (slug can be added later)
	share_url = f"/api/articles/{article_id}"
	return {"shared": True, "totalShares": count, "shareUrl": share_url}


@router.post("/{article_id}/save", response_model=dict)
async def toggle_save(article_id: str, current_user=Depends(get_current_user)):
	uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("sub") if isinstance(current_user, dict) else None)
	if not uid:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

	# save as users/{uid}/bookmarks/{article_id}
	bm_ref = firebase_service.db.collection("users").document(uid).collection("bookmarks").document(article_id)
	existing = bm_ref.get()
	if existing.exists:
		bm_ref.delete()
		saved = False
	else:
		bm_ref.set({"articleId": article_id, "createdAt": datetime.now(timezone.utc)})
		saved = True
	return {"saved": saved}


@router.post("/{article_id}/comments", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_comment(article_id: str, payload: dict, current_user=Depends(get_current_user)):
	# payload expected to include 'content'
	content = payload.get("content")
	if not content:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content required")
	uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("sub") if isinstance(current_user, dict) else None)
	if not uid:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

	comments_coll = firebase_service.db.collection("articles").document(article_id).collection("comments")
	doc_ref = comments_coll.document()
	now = datetime.now(timezone.utc)
	data = {"articleId": article_id, "authorId": uid, "content": content, "createdAt": now}
	doc_ref.set(data)
	return {"commentId": doc_ref.id, "articleId": article_id, "authorId": uid, "content": content, "createdAt": now}


@router.get("/{article_id}/comments", response_model=list)
async def list_comments(article_id: str, page: int = 1, pageSize: int = 50):
	comments_coll = firebase_service.db.collection("articles").document(article_id).collection("comments")
	docs = list(comments_coll.stream())
	# sort by createdAt
	docs.sort(key=lambda d: d.to_dict().get("createdAt") or datetime.min)
	start = (page - 1) * pageSize
	page_docs = docs[start:start+pageSize]
	out = []
	for doc in page_docs:
		d = doc.to_dict()
		out.append({"commentId": doc.id, "articleId": article_id, "authorId": d.get("authorId"), "content": d.get("content"), "createdAt": d.get("createdAt")})
	return out


@router.delete("/{article_id}/comments/{comment_id}")
async def delete_comment(article_id: str, comment_id: str, current_user=Depends(get_current_user)):
	comments_coll = firebase_service.db.collection("articles").document(article_id).collection("comments")
	ref = comments_coll.document(comment_id)
	doc = ref.get()
	if not doc.exists:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
	d = doc.to_dict()
	uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("sub") if isinstance(current_user, dict) else None)
	role = getattr(current_user, "role", None) or (current_user.get("role") if isinstance(current_user, dict) else None)
	if d.get("authorId") != uid and role != "admin":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete comment")
	ref.delete()
	return {"deleted": True}


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: str, payload: ArticleUpdateSchema, current_user=Depends(get_current_user)):
	doc_ref = firebase_service.db.collection("articles").document(article_id)
	doc = doc_ref.get()
	if not doc.exists:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

	existing = doc.to_dict()
	# Authorization: only author or admin can update
	uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("sub") if isinstance(current_user, dict) else None)
	if existing.get("authorId") and uid and existing.get("authorId") != uid:
		# try role check
		role = getattr(current_user, "role", None) or (current_user.get("role") if isinstance(current_user, dict) else None)
		if role != "admin":
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to modify this article")

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
	return ArticleResponse(
		articleId=a.article_id,
		title=a.title,
		slug=a.slug,
		content=a.content,
		authorId=a.author_id,
		tags=a.tags,
		published=a.published,
		createdAt=a.created_at,
		updatedAt=a.updated_at,
		likesCount=a.likes_count,
		views=a.views,
	)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: str, current_user=Depends(get_current_user)):
	doc_ref = firebase_service.db.collection("articles").document(article_id)
	doc = doc_ref.get()
	if not doc.exists:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

	existing = doc.to_dict()
	uid = getattr(current_user, "uid", None) or (current_user.get("uid") if isinstance(current_user, dict) else None) or (current_user.get("sub") if isinstance(current_user, dict) else None)
	if existing.get("authorId") and uid and existing.get("authorId") != uid:
		role = getattr(current_user, "role", None) or (current_user.get("role") if isinstance(current_user, dict) else None)
		if role != "admin":
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this article")

	doc_ref.delete()
	return None
