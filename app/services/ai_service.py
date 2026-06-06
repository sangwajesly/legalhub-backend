import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.services import gemini_service

logger = logging.getLogger(__name__)

_SUPPORTED_PROVIDERS = ["gemini", "huggingface", "openai", "cohere", "groq", "grok"]


def _gemini_model_list() -> List[str]:
    """Return an ordered list of Gemini models to attempt.

    Always starts with the primary GEMINI_MODEL, followed by any additional
    models listed in GEMINI_FALLBACK_MODELS (comma-separated). Duplicates are
    removed while preserving order.
    """
    primary = settings.GEMINI_MODEL.strip()
    fallbacks_raw = getattr(settings, "GEMINI_FALLBACK_MODELS", "")
    fallbacks = [m.strip() for m in fallbacks_raw.split(",") if m.strip()]

    seen: set = set()
    ordered: List[str] = []
    for m in [primary] + fallbacks:
        if m and m not in seen:
            seen.add(m)
            ordered.append(m)
    return ordered



def _extract_text_from_api_response(resp: Any) -> str:
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        for key in ("response", "text", "output", "answer"):  # common shapes
            if key in resp and isinstance(resp[key], str):
                return resp[key]
        for list_key in ("choices", "candidates", "outputs", "generations"):  # list shapes
            if list_key in resp and isinstance(resp[list_key], (list, tuple)) and resp[list_key]:
                first = resp[list_key][0]
                if isinstance(first, str):
                    return first
                if isinstance(first, dict):
                    for k in ("text", "content", "output", "generated_text"):
                        if k in first and isinstance(first[k], str):
                            return first[k]
        try:
            return str(resp)
        except Exception:
            return ""
    try:
        return str(resp)
    except Exception:
        return ""


def _normalize_provider_list(raw: str) -> List[str]:
    return [provider.strip().lower() for provider in raw.split(",") if provider.strip()]


async def _send_huggingface(prompt: str, model: str) -> Dict[str, Any]:
    if not settings.HUGGINGFACE_API_KEY:
        raise RuntimeError("Hugging Face API key is not configured.")

    endpoint = settings.HUGGINGFACE_API_URL or f"https://api-inference.huggingface.co/models/{model}"
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.2,
        },
        "options": {"wait_for_model": True},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        raw = response.json()

    if isinstance(raw, dict) and "error" in raw:
        raise RuntimeError(f"Hugging Face error: {raw['error']}")

    if isinstance(raw, list) and raw:
        first = raw[0]
        if isinstance(first, dict) and "generated_text" in first:
            return {"provider": "huggingface", "model": model, "response": first["generated_text"].strip(), "raw": raw}

    if isinstance(raw, dict):
        text = _extract_text_from_api_response(raw)
        return {"provider": "huggingface", "model": model, "response": text.strip(), "raw": raw}

    return {"provider": "huggingface", "model": model, "response": str(raw).strip(), "raw": raw}


async def _send_openai(prompt: str, model: str) -> Dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key is not configured.")

    endpoint = settings.OPENAI_API_URL or "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        raw = response.json()

    content = ""
    if isinstance(raw, dict):
        choices = raw.get("choices")
        if isinstance(choices, (list, tuple)) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content", "")
                else:
                    content = _extract_text_from_api_response(first)
        if not content:
            content = _extract_text_from_api_response(raw)

    return {"provider": "openai", "model": model, "response": content.strip(), "raw": raw}


async def _send_cohere(prompt: str, model: str) -> Dict[str, Any]:
    if not settings.COHERE_API_KEY:
        raise RuntimeError("Cohere API key is not configured.")

    endpoint = settings.COHERE_API_URL or "https://api.cohere.com/v1/generate"
    headers = {
        "Authorization": f"Bearer {settings.COHERE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 300,
        "temperature": 0.2,
        "return_likelihoods": "NONE",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        raw = response.json()

    text = ""
    if isinstance(raw, dict):
        generations = raw.get("generations")
        if isinstance(generations, (list, tuple)) and generations:
            first = generations[0]
            if isinstance(first, dict) and "text" in first:
                text = first["text"]
        if not text:
            text = _extract_text_from_api_response(raw)

    return {"provider": "cohere", "model": model, "response": text.strip(), "raw": raw}


async def _send_groq(prompt: str, model: str) -> Dict[str, Any]:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ API key is not configured.")

    endpoint = settings.GROQ_API_URL or "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Use standard chat models if the configured one looks incorrect or generic
    # Standard models are: llama-3.3-70b-versatile, llama-3.1-8b-instant, gemma2-9b-it
    groq_model = model
    if not groq_model or groq_model in ["groq-1-small", "default"]:
        groq_model = "llama-3.1-8b-instant"

    payload = {
        "model": groq_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        raw = response.json()

    content = ""
    if isinstance(raw, dict):
        choices = raw.get("choices")
        if isinstance(choices, (list, tuple)) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content", "")
        if not content:
            content = _extract_text_from_api_response(raw)

    return {"provider": "groq", "model": groq_model, "response": content.strip(), "raw": raw}


async def _send_grok(prompt: str, model: str) -> Dict[str, Any]:
    if not settings.GROK_API_KEY:
        raise RuntimeError("Grok API key is not configured.")

    endpoint = settings.GROK_API_URL or "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROK_API_KEY}",
        "Content-Type": "application/json",
    }
    
    grok_model = model
    if not grok_model or grok_model in ["grok-1", "default"]:
        grok_model = "grok-beta" # x.ai standard model name

    payload = {
        "model": grok_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        raw = response.json()

    content = ""
    if isinstance(raw, dict):
        choices = raw.get("choices")
        if isinstance(choices, (list, tuple)) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content", "")
        if not content:
            content = _extract_text_from_api_response(raw)

    return {"provider": "grok", "model": grok_model, "response": content.strip(), "raw": raw}


def _is_retryable_gemini_error(exc: Exception) -> bool:
    """Return True for transient Gemini errors worth retrying on another model.

    Retryable: 503 Service Unavailable, 429 Too Many Requests, 500 Internal.
    Non-retryable: 400 Bad Request, 401/403 auth errors (wrong key).
    """
    msg = str(exc).lower()
    return any(code in msg for code in ("503", "429", "500", "overload", "unavailable", "quota"))


async def send_message(
    prompt: str,
    model: Optional[str] = None,
    images: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    if settings.DEBUG_MOCK_GEMINI:
        logger.debug("Using mock AI response because DEBUG_MOCK_GEMINI is enabled")
        mock_res = await gemini_service.send_message(prompt, model=model, images=images)
        mock_res["provider"] = "mock"
        return mock_res

    last_error: Optional[Exception] = None

    # ---------------------------------------------------------------
    # PHASE 1 — Try every configured Gemini model in priority order
    # ---------------------------------------------------------------
    if settings.GOOGLE_API_KEY:
        # If a specific model was passed in, try that first; otherwise use the full list.
        gemini_models = [model] if model else _gemini_model_list()

        for gemini_model in gemini_models:
            try:
                logger.debug("Trying Gemini model: %s", gemini_model)
                result = await gemini_service.send_message(prompt, model=gemini_model, images=images)
                result["provider"] = "gemini"
                result["model"] = gemini_model
                return result
            except Exception as exc:
                last_error = exc
                if _is_retryable_gemini_error(exc):
                    logger.warning(
                        "Gemini model '%s' failed with retryable error, trying next Gemini model: %s",
                        gemini_model, exc,
                    )
                    continue  # try the next Gemini model
                else:
                    logger.warning(
                        "Gemini model '%s' failed with non-retryable error, skipping remaining Gemini models: %s",
                        gemini_model, exc,
                    )
                    break  # non-retryable (e.g. bad key) — skip straight to other providers

        logger.warning("All Gemini models exhausted. Trying external fallback providers.")
    else:
        logger.warning("GOOGLE_API_KEY not configured. Skipping Gemini entirely.")

    # ---------------------------------------------------------------
    # PHASE 2 — External providers (order from FALLBACK_AI_PROVIDERS)
    # ---------------------------------------------------------------
    provider_order = [
        p for p in _normalize_provider_list(settings.FALLBACK_AI_PROVIDERS)
        if p in _SUPPORTED_PROVIDERS and p != "gemini"
    ]

    for provider in provider_order:
        try:
            if provider == "huggingface":
                return await _send_huggingface(prompt, settings.HUGGINGFACE_MODEL)

            if provider == "openai":
                return await _send_openai(prompt, settings.OPENAI_MODEL)

            if provider == "cohere":
                return await _send_cohere(prompt, settings.COHERE_MODEL)

            if provider == "groq":
                return await _send_groq(prompt, settings.GROQ_MODEL)

            if provider == "grok":
                return await _send_grok(prompt, settings.GROK_MODEL)

        except Exception as exc:
            last_error = exc
            logger.warning(
                "AI provider '%s' failed, trying next fallback: %s",
                provider, exc,
            )
            continue

    error_message = (
        f"No AI provider succeeded. Last error: {last_error}"
        if last_error
        else "No AI provider configured. Set GOOGLE_API_KEY, HUGGINGFACE_API_KEY, OPENAI_API_KEY, or COHERE_API_KEY."
    )
    raise RuntimeError(error_message)


async def stream_send_message(prompt: str, model: Optional[str] = None):
    result = await send_message(prompt, model=model)
    text = result.get("response", "") if isinstance(result, dict) else str(result)
    yield {"model": model or settings.GEMINI_MODEL, "response": text, "raw": result}

