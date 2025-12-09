import logging
import asyncio
import asyncio
from typing import Optional, Any, Dict, List, Union
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
            if (
                list_key in resp
                and isinstance(resp[list_key], (list, tuple))
                and resp[list_key]
            ):
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




# Add this constant near the top of the file
GEMINI_REST_ENDPOINT = "https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"

# ... rest of the file ...

async def send_message(
    prompt: str, 
    model: Optional[str] = None, 
    images: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Send a prompt to Gemini (or return a mock response in DEV).
    
    Args:
        prompt: Text prompt
        model: Model name
        images: List of dicts checks {"mime_type": "image/jpeg", "data": b64_string}
    """
    model = model or settings.GEMINI_MODEL
    
    if settings.DEBUG_MOCK_GEMINI or not settings.GOOGLE_API_KEY:
        # MOCK PATH REMAINS UNCHANGED
        mock = {
            "model": model,
            "response": f"(mock) Answer to: {prompt[:200]}",
            "raw": {"mock": True},
        }
        logger.debug("Using mock Gemini response")
        return mock

    # 1. Construct the Correct URL and Headers
    # API Key is appended as a query parameter (standard for REST API access)
    url = f"{GEMINI_REST_ENDPOINT.format(model=model)}?key={settings.GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"} 
    
    # 2. Construct the Correct Payload (Contents and System Instruction)
    parts = [{"text": prompt}]
    
    # Append images if present
    if images:
        for img in images:
            parts.append({
                "inline_data": {
                    "mime_type": img["mime_type"],
                    "data": img["data"]
                }
            })

    payload = {
        # The prompt should be inside 'contents'
        "contents": [
            {"role": "user", "parts": parts}
        ],
        # System instructions/safety settings go here if needed,
        # but for simplicity, the prompt itself contains the system instructions.
    }

    logger.debug("Sending prompt to Gemini endpoint: %s", url)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status() # Raise error for 4xx/5xx status codes
            
            raw = r.json()
            
            # Use the correct extraction logic for the Gemini response
            # The structure is candidates[0].content.parts[0].text
            response_text = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            # Fallback to your generic extractor if the structure is unexpected
            if not response_text:
                response_text = _extract_text_from_api_response(raw) 
            
            return {"model": model, "response": response_text, "raw": raw}

        except httpx.HTTPStatusError as e:
            logger.error("Gemini API HTTP Error: %s - Response: %s", e, r.text)
            raise RuntimeError(f"Gemini API Error: {r.status_code} - {r.text}") from e
        except Exception as e:
            logger.error("Gemini API General Error: %s", e)
            raise RuntimeError(f"Failed to call Gemini API: {e}") from e





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
        raise RuntimeError(
            "GEMINI_API_URL not configured; enable DEBUG_MOCK_GEMINI or set GEMINI_API_URL"
        )

    url = f"{settings.GEMINI_API_URL}?key={settings.GOOGLE_API_KEY}"  # Append API key to URL
    headers = {"Content-Type": "application/json"}  # Remove Authorization header
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


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """Transcribe audio using Gemini Flash (multimodal)."""
    
    if settings.DEBUG_MOCK_GEMINI or not settings.GOOGLE_API_KEY:
        return "(Mock Transcription) This is a simulated transcription of the audio file."

    # Gemini API for multimodal content needs "parts" with "inlineData"
    url = f"{GEMINI_REST_ENDPOINT.format(model=settings.GEMINI_MODEL)}?key={settings.GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    import base64
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Transcribe this audio file exactly as it is spoken. Output only the transcription."},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_audio
                    }
                }
            ]
        }]
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            
            raw = r.json()
            # Extract text
            text = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return text.strip()
            
        except Exception as e:
            logger.error("Gemini Transcription Error: %s", e)
            raise RuntimeError(f"Transcription failed: {str(e)}")
