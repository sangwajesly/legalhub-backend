from fastapi.testclient import TestClient
from app.main import app

from app.services import firebase_service
from app.dependencies import get_current_user


def test_list_lawyers_mocked(monkeypatch):
    store = {}

    async def query_docs(collection, filters=None, limit=20, offset=0):
        docs = []
        for path, data in store.items():
            if path.startswith(f"{collection}/"):
                docs.append((path.split('/')[-1], data))
        return docs, len(docs)

    monkeypatch.setattr(firebase_service, 'query_collection', query_docs, raising=False)

    # put two lawyers
    store['lawyers/lawyer_1'] = {'displayName': 'Alice', 'practiceAreas': ['family'], 'hourlyRate': 60}
    store['lawyers/lawyer_2'] = {'displayName': 'Bob', 'practiceAreas': ['employment'], 'hourlyRate': 80}

    client = TestClient(app)
    r = client.get('/api/lawyers')
    assert r.status_code == 200
    data = r.json()
    assert data['total'] == 2
    assert len(data['lawyers']) == 2


def test_get_lawyer_mocked(monkeypatch):
    store = {'lawyers/lawyer_123': {'displayName': 'Jane', 'licenseNumber': 'BAR-123'}}

    async def get_doc(path):
        return store.get(path)

    monkeypatch.setattr(firebase_service, 'get_document', get_doc, raising=False)

    client = TestClient(app)
    r = client.get('/api/lawyers/lawyer_123')
    assert r.status_code == 200
    data = r.json()
    assert data['uid'] == 'lawyer_123'
    assert data['display_name'] in ('Jane', 'Jane')


def test_create_update_delete_lawyer(monkeypatch):
    store = {}

    async def set_doc(path, data):
        store[path] = data

    async def get_doc(path):
        return store.get(path)

    async def update_doc(path, data):
        if path in store:
            store[path].update(data)
        else:
            store[path] = data

    async def delete_doc(path):
        if path in store:
            del store[path]

    monkeypatch.setattr(firebase_service, 'set_document', set_doc, raising=False)
    monkeypatch.setattr(firebase_service, 'get_document', get_doc, raising=False)
    monkeypatch.setattr(firebase_service, 'update_document', update_doc, raising=False)
    monkeypatch.setattr(firebase_service, 'delete_document', delete_doc, raising=False)

    # override auth
    from app.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"uid": "lawyer_new", "is_admin": False}
    client = TestClient(app)

    # Create
    r = client.post('/api/lawyers', json={"display_name": "New Lawyer", "email": "new@law.com", "practice_areas": ["family"]})
    assert r.status_code == 200
    data = r.json()
    assert data['uid'] == 'lawyer_new'

    # Update
    r2 = client.put('/api/lawyers/lawyer_new', json={"bio": "Experienced"})
    assert r2.status_code == 200
    assert store.get('lawyers/lawyer_new').get('bio') == 'Experienced'

    # Delete
    r3 = client.delete('/api/lawyers/lawyer_new')
    assert r3.status_code == 200
    assert 'lawyers/lawyer_new' not in store

    app.dependency_overrides.clear()
