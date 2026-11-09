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


def test_mark_match_underway_returns_actionable_missing_cache_message(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        'set_match_underway_in_cache',
        lambda tournament_key, match_id: (_ for _ in ()).throw(
            ValueError("Local cache file not found. Click 'Update Local Cache' to create it.")
        ),
    )

    response = client.post(
        '/api/cache/match/underway',
        json={'tournament_key': 'abc', 'match_id': '1'},
        environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
    )

    assert response.status_code == 400
    assert "Update Local Cache" in response.get_json().get('error', '')


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


def test_notifications_admin_page_requires_loopback(client):
    response = client.get('/notifications/admin', environ_overrides={'REMOTE_ADDR': '10.0.0.10'})
    assert response.status_code == 403


def test_notifications_robots_returns_404_when_cache_missing(client, monkeypatch):
    monkeypatch.setattr(app_module, 'load_cached_tournament_data', lambda: None)
    response = client.get('/api/notifications/robots')
    assert response.status_code == 404
    assert "Local cache file not found" in response.get_json().get('error', '')


def test_notifications_robots_returns_robot_directory(client, monkeypatch):
    monkeypatch.setattr(app_module, 'load_cached_tournament_data', lambda: {'tournaments': {}})
    monkeypatch.setattr(app_module, 'build_robot_directory', lambda _: [{'robot_key': 'abc::crusher'}])
    response = client.get('/api/notifications/robots')
    assert response.status_code == 200
    assert response.get_json() == {'robots': [{'robot_key': 'abc::crusher'}]}


def test_notifications_subscribed_requires_robot_keys_array(client):
    response = client.post('/api/notifications/subscribed', json={'robot_keys': 'bad'})
    assert response.status_code == 400
    assert "robot_keys" in response.get_json().get('error', '')


def test_notifications_subscribed_returns_filtered_notifications(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        'list_notifications_for_robot_keys',
        lambda keys: [{'id': 'n1', 'robot_key': 'abc::crusher'}] if 'abc::crusher' in keys else [],
    )
    response = client.post('/api/notifications/subscribed', json={'robot_keys': ['abc::crusher']})
    assert response.status_code == 200
    assert response.get_json() == {'notifications': [{'id': 'n1', 'robot_key': 'abc::crusher'}]}


def test_notifications_send_requires_loopback(client):
    response = client.post(
        '/api/notifications/send',
        json={'robot_key': 'abc::crusher', 'type': 'eo_summon'},
        environ_overrides={'REMOTE_ADDR': '10.0.0.5'},
    )
    assert response.status_code == 403


def test_notifications_send_rejects_invalid_type(client):
    response = client.post(
        '/api/notifications/send',
        json={'robot_key': 'abc::crusher', 'type': 'bad_type'},
        environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
    )
    assert response.status_code == 400
    assert "must be one of" in response.get_json().get('error', '')


def test_notifications_send_creates_notification(client, monkeypatch):
    robot = {
        'robot_key': 'abc::crusher',
        'tournament_key': 'abc',
        'competition_name': 'Fairyweight',
        'bot_name': 'Crusher',
        'team_name': 'Team Alpha',
        'participant_id': 1,
    }
    monkeypatch.setattr(app_module, 'load_cached_tournament_data', lambda: {'tournaments': {'abc': {}}})
    monkeypatch.setattr(app_module, 'build_robot_directory', lambda _: [robot])
    monkeypatch.setattr(
        app_module,
        'create_notification',
        lambda **kwargs: {'id': 'n1', 'robot_key': kwargs['robot_key'], 'type': kwargs['notification_type']},
    )
    response = client.post(
        '/api/notifications/send',
        json={'robot_key': 'abc::crusher', 'type': 'eo_summon'},
        environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
    )
    assert response.status_code == 201
    assert response.get_json() == {'notification': {'id': 'n1', 'robot_key': 'abc::crusher', 'type': 'eo_summon'}}


def test_notifications_audit_requires_loopback(client):
    response = client.get('/api/notifications/audit', environ_overrides={'REMOTE_ADDR': '10.0.0.6'})
    assert response.status_code == 403


def test_notifications_audit_returns_all_notifications(client, monkeypatch):
    monkeypatch.setattr(app_module, 'list_all_notifications', lambda: [{'id': 'n1'}])
    response = client.get('/api/notifications/audit', environ_overrides={'REMOTE_ADDR': '127.0.0.1'})
    assert response.status_code == 200
    assert response.get_json() == {'notifications': [{'id': 'n1'}]}


def test_notifications_match_queue_call_requires_loopback(client):
    response = client.post(
        '/api/notifications/match/queue-call',
        json={'tournament_key': 'abc', 'match_id': '1'},
        environ_overrides={'REMOTE_ADDR': '10.0.0.2'},
    )
    assert response.status_code == 403


def test_notifications_match_queue_call_requires_fields(client):
    response = client.post(
        '/api/notifications/match/queue-call',
        json={'tournament_key': 'abc'},
        environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
    )
    assert response.status_code == 400
    assert "required" in response.get_json().get('error', '').lower()


def test_notifications_match_queue_call_creates_two_notifications(client, monkeypatch):
    cache_payload = {
        'tournaments': {
            'abc': {
                'matches': [{'id': 1, 'player1_id': 11, 'player2_id': 22}],
                'participants': [{'id': 11, 'name': 'Crusher'}, {'id': 22, 'name': 'Smasher'}],
            }
        }
    }
    robot_directory = [
        {
            'robot_key': 'abc::crusher',
            'tournament_key': 'abc',
            'competition_name': 'Fairyweight',
            'bot_name': 'Crusher',
            'team_name': 'Team A',
            'participant_id': 11,
        },
        {
            'robot_key': 'abc::smasher',
            'tournament_key': 'abc',
            'competition_name': 'Fairyweight',
            'bot_name': 'Smasher',
            'team_name': 'Team B',
            'participant_id': 22,
        },
    ]

    monkeypatch.setattr(app_module, 'load_cached_tournament_data', lambda: cache_payload)
    monkeypatch.setattr(app_module, 'build_robot_directory', lambda _: robot_directory)
    monkeypatch.setattr(
        app_module,
        'create_notification',
        lambda **kwargs: {'id': f"n-{kwargs['robot_key']}", 'robot_key': kwargs['robot_key'], 'type': kwargs['notification_type']},
    )

    response = client.post(
        '/api/notifications/match/queue-call',
        json={'tournament_key': 'abc', 'match_id': '1'},
        environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert len(payload.get('notifications', [])) == 2
    assert {n['robot_key'] for n in payload['notifications']} == {'abc::crusher', 'abc::smasher'}
