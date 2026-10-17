"""amd_client against a monkeypatched requests.post — no network."""

import dataclasses

import pytest
import requests

from app import amd_client
from app.models import InspectionError

MESSAGES = [{"role": "user", "content": "ping"}]


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", headers=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


@pytest.fixture
def capture_post(monkeypatch):
    calls = {}

    def install(response=None, exc=None):
        def fake_post(url, headers, json, timeout):
            calls.update(url=url, headers=headers, json=json, timeout=timeout)
            if exc:
                raise exc
            return response

        monkeypatch.setattr(amd_client.requests, "post", fake_post)
        return calls

    return install


def test_success_returns_content_and_sends_openai_shape(settings, capture_post):
    calls = capture_post(FakeResponse(payload={"choices": [{"message": {"content": "pong"}}]}))
    assert amd_client.chat_completion(settings, MESSAGES) == "pong"
    assert calls["url"] == "https://amd.example.test/v1/chat/completions"
    assert calls["headers"]["Authorization"] == "Bearer test-key"
    assert calls["json"]["model"] == "test-vlm"
    assert calls["json"]["temperature"] == 0.1 and calls["json"]["max_tokens"] == 1024


def test_no_auth_header_when_key_empty(settings, capture_post):
    calls = capture_post(FakeResponse(payload={"choices": [{"message": {"content": "pong"}}]}))
    amd_client.chat_completion(dataclasses.replace(settings, api_key=""), MESSAGES)
    assert "Authorization" not in calls["headers"]


def test_connection_error_is_endpoint_unreachable(settings, capture_post):
    capture_post(exc=requests.ConnectionError("dns failure"))
    with pytest.raises(InspectionError) as exc_info:
        amd_client.chat_completion(settings, MESSAGES)
    assert exc_info.value.stage == "endpoint_unreachable"
    assert "check AMD_API_URL" in exc_info.value.detail
    assert "test-key" not in exc_info.value.detail


def test_timeout_is_endpoint_timeout_not_bad_url(settings, capture_post):
    capture_post(exc=requests.ReadTimeout("read timed out"))
    with pytest.raises(InspectionError) as exc_info:
        amd_client.chat_completion(settings, MESSAGES, timeout_s=90)
    assert exc_info.value.stage == "endpoint_timeout"
    assert "within 90s" in exc_info.value.detail and "AMD_API_URL" not in exc_info.value.detail


def test_http_error_is_endpoint_error(settings, capture_post):
    capture_post(FakeResponse(status_code=401, text="invalid api key"))
    with pytest.raises(InspectionError) as exc_info:
        amd_client.chat_completion(settings, MESSAGES)
    assert exc_info.value.stage == "endpoint_error" and "401" in exc_info.value.detail


def test_non_chat_completion_body_is_parse_failed(settings, capture_post):
    capture_post(FakeResponse(payload={"unexpected": True}, text='{"unexpected": true}'))
    with pytest.raises(InspectionError) as exc_info:
        amd_client.chat_completion(settings, MESSAGES)
    assert exc_info.value.stage == "parse_failed"


def _sequence(monkeypatch, responses):
    calls, sleeps = [], []
    monkeypatch.setattr(amd_client.requests, "post", lambda *a, **kw: calls.append(1) or responses.pop(0))
    monkeypatch.setattr(amd_client.time, "sleep", sleeps.append)
    return calls, sleeps


def test_429_backs_off_then_succeeds(settings, monkeypatch):
    ok = FakeResponse(payload={"choices": [{"message": {"content": "pong"}}]})
    calls, sleeps = _sequence(monkeypatch, [FakeResponse(429, headers={"Retry-After": "1"}), ok])
    assert amd_client.chat_completion(settings, MESSAGES) == "pong"
    assert len(calls) == 2 and sleeps == [1.0]


def test_persistent_429_gives_up_as_endpoint_error(settings, monkeypatch):
    calls, sleeps = _sequence(monkeypatch, [FakeResponse(429, text="rate limited")] * 3)
    with pytest.raises(InspectionError) as exc_info:
        amd_client.chat_completion(settings, MESSAGES)
    assert exc_info.value.stage == "endpoint_error" and "429" in exc_info.value.detail
    assert len(calls) == amd_client.RATE_LIMIT_ATTEMPTS and len(sleeps) == amd_client.RATE_LIMIT_ATTEMPTS - 1


def test_mock_mode_makes_no_http_call(settings, monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("MOCK_MODE must not make an HTTP call")

    monkeypatch.setattr(amd_client.requests, "post", forbidden)
    out = amd_client.chat_completion(dataclasses.replace(settings, mock_mode=True), MESSAGES)
    assert "MOCK_MODE" in out
