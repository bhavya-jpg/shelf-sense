"""Thin wrapper around the AMD-hosted vLLM OpenAI-compatible chat-completions endpoint (§7.3)."""

import json
import logging
import time

import requests

from app.config import Settings
from app.models import InspectionError

log = logging.getLogger(__name__)

TIMEOUT_S = 90
RATE_LIMIT_ATTEMPTS = 3
MAX_RETRY_AFTER_S = 10.0


def _retry_after_s(resp, default: float) -> float:
    try:
        return min(float(resp.headers.get("Retry-After", default)), MAX_RETRY_AFTER_S)
    except (TypeError, ValueError):
        return default

# MOCK_MODE only: a fixed, clearly-labelled fake response for offline UI development.
# It is NOT a model output and must never appear in a demo or the deployed app (§8).
MOCK_RESPONSE = json.dumps(
    {
        "items": [
            {"item_id": "brand_a_cereal", "detected_count": 6, "status": "present", "confidence": 90, "note": "MOCK"},
            {"item_id": "brand_b_cereal", "detected_count": 2, "status": "partial", "confidence": 80, "note": "MOCK"},
            {"item_id": "promo_sign", "detected_count": 1, "status": "present", "confidence": 85, "note": "MOCK"},
        ],
        "notes": "MOCK_MODE: fixed fake response, no AMD inference call was made.",
    }
)


def chat_completion(
    settings: Settings,
    messages: list[dict],
    *,
    temperature: float = 0.1,
    max_tokens: int = 1024,
    timeout_s: float = TIMEOUT_S,
) -> str:
    """POST one chat completion and return choices[0].message.content."""
    if settings.mock_mode:
        log.warning("MOCK_MODE is on — returning a fixed fake response, no AMD call made")
        return MOCK_RESPONSE

    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    body = {
        "model": settings.model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for attempt in range(1, RATE_LIMIT_ATTEMPTS + 1):
        log.info("Calling AMD endpoint host=%s model=%s", settings.endpoint_host, settings.model_name)
        try:
            resp = requests.post(
                f"{settings.api_url}/chat/completions", headers=headers, json=body, timeout=timeout_s
            )
        except requests.Timeout as exc:
            raise InspectionError(
                "endpoint_timeout",
                f"The AMD inference endpoint at {settings.endpoint_host} did not respond within "
                f"{timeout_s:.0f}s ({type(exc).__name__}) — the shared endpoint may be busy; retry shortly",
            ) from exc
        except requests.RequestException as exc:
            raise InspectionError(
                "endpoint_unreachable",
                f"Could not reach the AMD inference endpoint at {settings.endpoint_host} "
                f"({type(exc).__name__}) — check AMD_API_URL",
            ) from exc
        if resp.status_code != 429 or attempt == RATE_LIMIT_ATTEMPTS:
            break
        # Token Factory rate limits are shared per key: back off and retry on 429.
        delay = _retry_after_s(resp, default=2.0 * attempt)
        log.warning("AMD endpoint rate-limited (429), retrying in %.1fs", delay)
        time.sleep(delay)

    if resp.status_code != 200:
        raise InspectionError(
            "endpoint_error",
            f"AMD endpoint returned HTTP {resp.status_code}: {resp.text[:300]}",
        )

    try:
        content = resp.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise InspectionError(
            "parse_failed", f"Response is not a chat completion: {resp.text[:300]}"
        ) from exc
    if not isinstance(content, str):
        raise InspectionError("parse_failed", "choices[0].message.content is not a string")
    return content
