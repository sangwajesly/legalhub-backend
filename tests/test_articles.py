import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def patch_firebase(monkeypatch):
    class DummyDoc:
        def __init__(self, data, id_):
            self._data = data
            self.id = id_

        def to_dict(self):
            return self._data

        @property
        def exists(self):
            return bool(self._data)

    class DummyCollection:
        def __init__(self):
            self._store = {}

        def document(self, doc_id=None):
            if doc_id is None:
                # create new id
                doc_id = f"doc_{len(self._store)+1}"

            class Ref:
                def __init__(self, coll, id_):
                    self.coll = coll
                    self.id = id_

                def set(self, data):
                    self.coll._store[self.id] = data

                def get(self):
                    data = self.coll._store.get(self.id, {})
                    return DummyDoc(data, self.id)

                def update(self, data):
                    if self.id in self.coll._store:
                        self.coll._store[self.id].update(data)
                    else:
                        raise Exception("Not found")

                def delete(self):
                    if self.id in self.coll._store:
                        del self.coll._store[self.id]

                def collection(self, _):
                    return self.coll

            return Ref(self, doc_id)

        def stream(self):
            for k, v in self._store.items():
                yield DummyDoc(v, k)

    class DummyDB:
        def __init__(self):
            self.collections = {}

        def collection(self, name):
            if name not in self.collections:
                self.collections[name] = DummyCollection()
            return self.collections[name]

    dummy_db = DummyDB()

    # monkeypatch firebase_service.db used in routes
    import app.services.firebase_service as fs_mod

    # replace the db client with dummy
    fs_mod.firebase_service.db = dummy_db

    # override auth dependency via FastAPI app overrides (like other tests)
    from app.dependencies import get_current_user, get_optional_user
    from app.main import app as _app

    _app.dependency_overrides[get_current_user] = lambda: {
        "uid": "user_1",
        "role": "user",
    }
    _app.dependency_overrides[get_optional_user] = lambda: {
        "uid": "user_1",
        "role": "user",
    }

    yield

    # cleanup overrides after each test
    _app.dependency_overrides.clear()


def test_create_and_get_article():
    client = TestClient(app)

    payload = {
        "title": "Test Article",
        "content": "This is a test article.",
        "tags": ["test"],
        "published": True,
    }

    # create
    r = client.post("/api/articles/", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == payload["title"] or body["title"] == payload["title"]
    # slug should be present and non-empty
    assert "slug" in body and body["slug"]
    article_id = body["articleId"]

    # get
    r2 = client.get(f"/api/articles/{article_id}")
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["articleId"] == article_id
    assert "content" in b2
    # also ensure retrieval by slug works
    slug = body.get("slug")
    if slug:
        r3 = client.get(f"/api/articles/{slug}")
        assert r3.status_code == 200
        assert r3.json()["articleId"] == article_id


def test_list_update_delete_article():
    client = TestClient(app)

    payload = {
        "title": "Another Article",
        "content": "Body",
        "tags": [],
        "published": False,
    }

    r = client.post("/api/articles/", json=payload)
    assert r.status_code == 201
    article_id = r.json()["articleId"]
    slug = r.json().get("slug")

    # list
    r2 = client.get("/api/articles/?page=1&pageSize=10")
    assert r2.status_code == 200
    data = r2.json()
    assert data["total"] >= 1

    # update (as same user)
    upd = {"title": "Updated Title"}
    r3 = client.put(f"/api/articles/{article_id}", json=upd)
    assert r3.status_code == 200
    assert r3.json()["title"] == "Updated Title"

    # delete
    r4 = client.delete(f"/api/articles/{article_id}")
    assert r4.status_code == 204


def test_like_save_and_comments(monkeypatch):
    from app.main import app as _app

    # app.dependency_overrides set in fixture
    client = TestClient(_app)

    # create article
    payload = {"title": "Interact", "content": "Body", "tags": [], "published": True}
    r = client.post("/api/articles/", json=payload)
    assert r.status_code == 201
    aid = r.json()["articleId"]

    # like
    r1 = client.post(f"/api/articles/{aid}/like")
    assert r1.status_code == 200
    assert r1.json()["liked"] is True

    # like again (toggle off)
    r2 = client.post(f"/api/articles/{aid}/like")
    assert r2.status_code == 200
    assert r2.json()["liked"] is False

    # save/bookmark
    r3 = client.post(f"/api/articles/{aid}/save")
    assert r3.status_code == 200
    assert r3.json()["saved"] is True

    # add comment
    r4 = client.post(f"/api/articles/{aid}/comments", json={"content": "Nice article"})
    assert r4.status_code == 201
    cid = r4.json()["commentId"]

    # list comments
    r5 = client.get(f"/api/articles/{aid}/comments")
    assert r5.status_code == 200
    comments = r5.json()
    assert any(c["commentId"] == cid for c in comments)

    # delete comment
    r6 = client.delete(f"/api/articles/{aid}/comments/{cid}")
    assert r6.status_code == 200
    assert r6.json()["deleted"] is True


def test_share_and_role_creation(monkeypatch):
    from app.main import app as _app

    client = TestClient(_app)

    # create as lawyer role
    from app.dependencies import get_current_user

    _app.dependency_overrides[get_current_user] = lambda: {
        "uid": "lawyer_1",
        "role": "lawyer",
    }
    payload = {
        "title": "By Lawyer",
        "content": "Law content",
        "tags": [],
        "published": True,
    }
    r = client.post("/api/articles/", json=payload)
    assert r.status_code == 201
    aid = r.json()["articleId"]
    slug = r.json().get("slug")

    # share anonymously
    _app.dependency_overrides.clear()
    r2 = client.post(f"/api/articles/{aid}/share", json={"platform": "twitter"})
    assert r2.status_code == 200
    assert r2.json()["shared"] is True
    assert r2.json()["totalShares"] >= 1
    # shareUrl should prefer the slug when available
    share_url = r2.json().get("shareUrl")
    if slug:
        assert share_url.endswith(f"/{slug}")

    # share as a user
    _app.dependency_overrides[get_current_user] = lambda: {
        "uid": "user_2",
        "role": "user",
    }
    r3 = client.post(f"/api/articles/{aid}/share", json={"platform": "facebook"})
    assert r3.status_code == 200
    assert r3.json()["totalShares"] >= 2

    _app.dependency_overrides.clear()
