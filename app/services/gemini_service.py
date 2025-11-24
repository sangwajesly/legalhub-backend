import os
from typing import Optional
import httpx
from app.config import settings


async def send_message(prompt: str, model: Optional[str] = None) -> dict:
    """Send a prompt to Gemini (or return a mock response in DEV)."""
    model = model or settings.GEMINI_MODEL
    if settings.DEBUG_MOCK_GEMINI or not settings.GOOGLE_API_KEY:
        # Return a deterministic mock response for local dev and tests
        return {
            "model": model,
            "response": f"(mock) Answer to: {prompt[:200]}",
            "raw": {"mock": True},
        }

    # If a real API URL is provided, call it. This implementation expects the user to
    # set `GEMINI_API_URL` to a compatible endpoint. For safety, we don't hardcode
    # provider-specific request shapes here.
    if not settings.GEMINI_API_URL:
        raise RuntimeError("GEMINI_API_URL not configured; enable DEBUG_MOCK_GEMINI or set GEMINI_API_URL")

    url = settings.GEMINI_API_URL
    headers = {"Authorization": f"Bearer {settings.GOOGLE_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "prompt": prompt}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()
