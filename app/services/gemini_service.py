import logging
import asyncio
from typing import Optional, Any, Dict
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def _extract_text_from_api_response(resp: Any) -> str:
    """Try to extract a human-readable response text from various API shapes.

    This is intentionally permissive: many generative APIs return results in
    different keys (`response`, `text`, `output`, `candidates`, ...). We
    normalize to a single string to simplify downstream code.
    """
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        # common keys
        for key in ("response", "text", "output", "answer"):
            if key in resp and isinstance(resp[key], str):
                return resp[key]

        # Some APIs return choices or candidates as lists
        for list_key in ("choices", "candidates", "outputs"):
            if list_key in resp and isinstance(resp[list_key], (list, tuple)) and resp[list_key]:
                first = resp[list_key][0]
                if isinstance(first, str):
                    return first
                if isinstance(first, dict):
                    # try common nested keys
                    for k in ("text", "content", "output"):
                        if k in first and isinstance(first[k], str):
                            return first[k]

        # fallback to string conversion
        try:
            return str(resp)
        except Exception:
            return ""
    # other types
    try:
        return str(resp)
    except Exception:
        return ""


async def send_message(prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Send a prompt to Gemini (or return a mock response in DEV).

    Returns a normalized dict: {"model": ..., "response": <str>, "raw": <original>}
    """
    model = model or settings.GEMINI_MODEL
    if settings.DEBUG_MOCK_GEMINI or not settings.GOOGLE_API_KEY:
        # Return a deterministic mock response for local dev and tests
        mock = {"model": model, "response": f"(mock) Answer to: {prompt[:200]}", "raw": {"mock": True}}
        logger.debug("Using mock Gemini response")
        return mock

    if not settings.GEMINI_API_URL:
        raise RuntimeError("GEMINI_API_URL not configured; enable DEBUG_MOCK_GEMINI or set GEMINI_API_URL")

    url = f"{settings.GEMINI_API_URL}?key={settings.GOOGLE_API_KEY}" # Append API key to URL
    headers = {"Content-Type": "application/json"} # Remove Authorization header
    payload = {"model": model, "prompt": prompt}

    logger.debug("Sending prompt to Gemini endpoint: %s", url)
    print(f"Gemini API URL: {url}")
    print(f"Gemini Request Headers: {headers}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        raw = r.json()
        response_text = _extract_text_from_api_response(raw)
        return {"model": model, "response": response_text, "raw": raw}


async def stream_send_message(prompt: str, model: Optional[str] = None):
    """Stream a prompt to Gemini, yielding normalized chunks as they arrive.

    Yields dicts of the form {"model": ..., "response": <str>, "raw": <original_or_none>}.
    In DEV mode this yields a few mock chunks to simulate streaming.
    """
    model = model or settings.GEMINI_MODEL
    # Mock streaming for dev/tests
    if settings.DEBUG_MOCK_GEMINI or not settings.GOOGLE_API_KEY:
        full = f"(mock) Streaming answer to: {prompt[:200]}"
        # split into simple chunks (by sentences/words)
        parts = full.split(" ")
        for p in parts:
            await asyncio.sleep(0)  # allow event loop to schedule
            yield {"model": model, "response": p + " ", "raw": {"mock": True}}
        return

    if not settings.GEMINI_API_URL:
        raise RuntimeError("GEMINI_API_URL not configured; enable DEBUG_MOCK_GEMINI or set GEMINI_API_URL")

    url = f"{settings.GEMINI_API_URL}?key={settings.GOOGLE_API_KEY}" # Append API key to URL
    headers = {"Content-Type": "application/json"} # Remove Authorization header
    payload = {"model": model, "prompt": prompt}

    print(f"Gemini API URL (stream): {url}")
    print(f"Gemini Request Headers (stream): {headers}")
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            # httpx provides an async iterator over text chunks
            async for chunk in resp.aiter_text():
                if not chunk:
                    continue
                # try to parse chunk as json, but fallback to raw text
                parsed = None
                try:
                    parsed = httpx.Response(200, content=chunk).json()
                except Exception:
                    parsed = None
                if parsed:
                    text = _extract_text_from_api_response(parsed)
                    yield {"model": model, "response": text, "raw": parsed}
                else:
                    yield {"model": model, "response": chunk, "raw": None}
