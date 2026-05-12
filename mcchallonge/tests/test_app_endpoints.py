import json
from pathlib import Path

import pytest

import mcchallonge.app as app_module


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


def test_queue_page_renders_for_non_loopback(client):
    response = client.get('/queue', environ_overrides={'REMOTE_ADDR': '10.0.0.5'})
    assert response.status_code == 200
    assert b'Match Queue' in response.data


def test_api_underway_returns_refresh_payload(client, monkeypatch):
    payload = {
        'generated_at': '2026-05-12 10:00:00',
        'banners': [{'filename': 'demo.png'}],
    }
    monkeypatch.setattr(app_module, '_refresh_underway_from_cache', lambda: payload)

    response = client.get('/api/underway')

    assert response.status_code == 200
    assert response.get_json() == payload


def test_cache_update_requires_loopback(client):
    response = client.post('/api/cache/update', json={}, environ_overrides={'REMOTE_ADDR': '10.1.1.10'})
    assert response.status_code == 403


def test_cache_update_returns_500_when_no_tournament_ids(client, monkeypatch):
    monkeypatch.setitem(app_module.app.config, 'TOURNAMENT_IDS', [])

    response = client.post('/api/cache/update', json={}, environ_overrides={'REMOTE_ADDR': '127.0.0.1'})

    assert response.status_code == 500
    assert 'No tournament IDs are configured.' in response.get_json().get('error', '')


def test_mark_match_underway_requires_fields(client):
    response = client.post(
        '/api/cache/match/underway',
        json={'tournament_key': 'abc'},
        environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
    )
    assert response.status_code == 400
    assert "required" in response.get_json().get('error', '').lower()


def test_mark_match_underway_success(client, monkeypatch):
    data = {'tournaments': {'abc': {'matches': [{'id': 1, 'state': 'open', 'underway_at': '2026-05-12T10:00:00'}]}}}

    monkeypatch.setattr(app_module, 'set_match_underway_in_cache', lambda tournament_key, match_id: data)
    monkeypatch.setattr(app_module, 'generate_underway_banners', lambda payload: {'count': 1, 'banners': []})

    response = client.post(
        '/api/cache/match/underway',
        json={'tournament_key': 'abc', 'match_id': '1'},
        environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
    )

    assert response.status_code == 200
    assert response.get_json() == data


def test_clear_match_underway_requires_loopback(client):
    response = client.post(
        '/api/cache/match/underway/clear',
        json={'tournament_key': 'abc', 'match_id': '1'},
        environ_overrides={'REMOTE_ADDR': '192.168.1.10'},
    )
    assert response.status_code == 403


def test_clear_match_underway_success(client, monkeypatch):
    data = {'tournaments': {'abc': {'matches': [{'id': 1, 'underway_at': None}]}}}

    monkeypatch.setattr(app_module, 'clear_match_underway_in_cache', lambda tournament_key, match_id: data)
    monkeypatch.setattr(app_module, 'generate_underway_banners', lambda payload: {'count': 0, 'banners': []})

    response = client.post(
        '/api/cache/match/underway/clear',
        json={'tournament_key': 'abc', 'match_id': '1'},
        environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
    )

    assert response.status_code == 200
    assert response.get_json() == data


def test_cache_clear_deletes_file_for_loopback(client, monkeypatch, tmp_path):
    cache_file = tmp_path / 'cache.json'
    cache_file.write_text(json.dumps({'tournaments': {}}), encoding='utf-8')

    monkeypatch.setattr(app_module, 'get_cache_file_path', lambda: cache_file)

    response = client.post('/api/cache/clear', json={}, environ_overrides={'REMOTE_ADDR': '127.0.0.1'})

    assert response.status_code == 200
    assert response.get_json().get('message') == 'Cache cleared.'
    assert not cache_file.exists()
