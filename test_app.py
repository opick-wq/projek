# test_app.py
from app import app


def test_home():
    """
    Menguji endpoint utama (/).
    """
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Demo Flask REST API' in response.data


def test_status():
    """
    Menguji endpoint status (/status).
    """
    client = app.test_client()
    response = client.get('/status')
    assert response.status_code == 200

    # Bandingkan dictionary, bukan string mentah
    data = response.get_json()
    assert data["status"] == "ok"
