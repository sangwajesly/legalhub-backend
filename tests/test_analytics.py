from fastapi.testclient import TestClient
from app.main import app


def test_analytics_overview_and_cases(monkeypatch):
    # create a dummy in-memory DB like other tests
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
                doc_id = f"id_{len(self._store)+1}"
            class Ref:
                def __init__(self, coll, id_):
                    self.coll = coll
                    self.id = id_

                def set(self, data):
                    self.coll._store[self.id] = data

                def get(self):
                    return DummyDoc(self.coll._store.get(self.id, {}), self.id)

                def stream(self):
                    for k, v in self.coll._store.items():
                        yield DummyDoc(v, k)

                def update(self, data):
                    if self.id in self.coll._store:
                        self.coll._store[self.id].update(data)

                def delete(self):
                    if self.id in self.coll._store:
                        del self.coll._store[self.id]

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

    # populate users, lawyers, cases, bookings, articles
    users = dummy_db.collection("users")
    users.document("u1").set({"email": "a@a.com"})
    users.document("u2").set({"email": "b@b.com"})

    lawyers = dummy_db.collection("lawyers")
    lawyers.document("l1").set({"displayName": "L1"})

    cases = dummy_db.collection("cases")
    cases.document("c1").set({"status": "open"})
    cases.document("c2").set({"status": "closed"})
    cases.document("c3").set({"status": "open"})

    bookings = dummy_db.collection("bookings")
    bookings.document("b1").set({"status": "confirmed"})

    articles = dummy_db.collection("articles")
    articles.document("a1").set({"title": "One"})

    import app.services.firebase_service as fs_mod
    fs_mod.firebase_service.db = dummy_db

    # override auth as admin
    from app.dependencies import get_current_user
    from types import SimpleNamespace
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(uid="admin", role="admin")

    client = TestClient(app)

    r = client.get("/api/analytics/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["totalUsers"] == 2
    assert body["totalLawyers"] == 1
    assert body["totalCases"] == 3
    assert body["totalBookings"] == 1
    assert body["totalArticles"] == 1

    r2 = client.get("/api/analytics/cases/status")
    assert r2.status_code == 200
    counts = r2.json()["counts"]
    assert counts.get("open") == 2
    assert counts.get("closed") == 1

    app.dependency_overrides.clear()
