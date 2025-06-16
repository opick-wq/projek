# test_app.py
from app import app

def test_home():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Selamat datang di Flask REST API!' in response.data

def test_status():
    client = app.test_client()
    response = client.get('/status')
    assert response.status_code == 200
    assert b'"status": "ok"' in response.data
