import pytest
import json
from app import app
import tempfile
import os

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_initialize_chat_missing_fields(client):
    """Test chat initialization with missing fields"""
    response = client.post('/chat/initialize',
                         json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_query_invalid_session(client):
    """Test query with invalid session"""
    response = client.post('/chat/invalid_session/query',
                         json={'query': 'test query'})
    assert response.status_code == 404