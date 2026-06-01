import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.services import gemini_service

logger = logging.getLogger(__name__)

_SUPPORTED_PROVIDERS = ["gemini", "huggingface", "openai", "cohere", "groq", "grok"]


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
    # Standard models are: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it, llama3-8b-8192
    groq_model = model
    if not groq_model or groq_model in ["groq-1-small", "default"]:
        groq_model = "mixtral-8x7b-32768"

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

    provider_order = ["gemini"]
    provider_order.extend(
        [p for p in _normalize_provider_list(settings.FALLBACK_AI_PROVIDERS) if p in _SUPPORTED_PROVIDERS and p != "gemini"]
    )

    last_error: Optional[Exception] = None
    for provider in provider_order:
        try:
            if provider == "gemini":
                if not settings.GOOGLE_API_KEY:
                    raise RuntimeError("Gemini API key is not configured.")
                return await gemini_service.send_message(prompt, model=model, images=images)

            if provider == "huggingface":
                return await _send_huggingface(prompt, model or settings.HUGGINGFACE_MODEL)

            if provider == "openai":
                return await _send_openai(prompt, model or settings.OPENAI_MODEL)

            if provider == "cohere":
                return await _send_cohere(prompt, model or settings.COHERE_MODEL)

            if provider == "groq":
                return await _send_groq(prompt, model or settings.GROQ_MODEL)

            if provider == "grok":
                return await _send_grok(prompt, model or settings.GROK_MODEL)

        except Exception as exc:
            last_error = exc
            logger.warning(
                "AI provider '%s' failed, trying next fallback: %s",
                provider,
                exc,
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
