"""
auditor/llm_runner.py
Unified runner for OpenAI, Anthropic, and Google Gemini APIs.
Handles rate-limiting, retries, and response normalisation.
"""

import time
import random
from typing import Dict, Optional
from config import (
    BUSINESS_SYSTEM_PROMPT, MAX_TOKENS, TEMPERATURE,
    RATE_LIMIT_DELAY, LLM_MODELS
)


# ── Base result schema ────────────────────────────────────────────────────────

def _ok(model: str, response: str, tokens: int = 0) -> Dict:
    return {"model": model, "response": response,
            "tokens_used": tokens, "error": None, "success": True}


def _err(model: str, message: str) -> Dict:
    return {"model": model, "response": "", "tokens_used": 0,
            "error": message, "success": False}


# ── Individual LLM callers ────────────────────────────────────────────────────

def call_openai(prompt: str, model_key: str = "GPT-4o",
                api_key: str = "") -> Dict:
    model_id = LLM_MODELS.get(model_key, "gpt-4o")
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": BUSINESS_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        text = resp.choices[0].message.content.strip()
        tokens = resp.usage.total_tokens
        return _ok(model_key, text, tokens)
    except Exception as exc:
        return _err(model_key, str(exc))


def call_anthropic(prompt: str, model_key: str = "Claude Sonnet",
                   api_key: str = "") -> Dict:
    model_id = LLM_MODELS.get(model_key, "claude-sonnet-4-5")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model_id,
            max_tokens=MAX_TOKENS,
            system=BUSINESS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        tokens = resp.usage.input_tokens + resp.usage.output_tokens
        return _ok(model_key, text, tokens)
    except Exception as exc:
        return _err(model_key, str(exc))


def call_gemini(prompt: str, model_key: str = "Gemini Pro",
                api_key: str = "") -> Dict:
    model_id = LLM_MODELS.get(model_key, "gemini-1.5-pro")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_id,
            system_instruction=BUSINESS_SYSTEM_PROMPT,
        )
        resp = model.generate_content(
            prompt,
            generation_config={"temperature": TEMPERATURE,
                                "max_output_tokens": MAX_TOKENS},
        )
        return _ok(model_key, resp.text.strip())
    except Exception as exc:
        return _err(model_key, str(exc))


# ── Provider dispatcher ───────────────────────────────────────────────────────

def call_llm(prompt: str, model_key: str,
             api_keys: Dict[str, str],
             retries: int = 2) -> Dict:
    """
    Dispatch a prompt to the correct provider with retry logic.

    api_keys must contain:
        { "openai": "sk-...", "anthropic": "sk-ant-...", "google": "AIza..." }
    """
    from config import LLM_PROVIDERS
    provider = LLM_PROVIDERS.get(model_key, "openai")

    for attempt in range(retries + 1):
        if provider == "openai":
            result = call_openai(prompt, model_key, api_keys.get("openai", ""))
        elif provider == "anthropic":
            result = call_anthropic(prompt, model_key, api_keys.get("anthropic", ""))
        elif provider == "google":
            result = call_gemini(prompt, model_key, api_keys.get("google", ""))
        else:
            return _err(model_key, f"Unknown provider: {provider}")

        if result["success"]:
            break
        if attempt < retries:
            # Exponential back-off with jitter
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)

    time.sleep(RATE_LIMIT_DELAY)   # polite rate limiting
    return result


# ── Batch runner ──────────────────────────────────────────────────────────────

def run_prompt_on_all_models(
    prompt: str,
    selected_models: list,
    api_keys: Dict[str, str],
) -> Dict[str, Dict]:
    """Run one prompt across multiple models; return dict keyed by model name."""
    results = {}
    for model_key in selected_models:
        results[model_key] = call_llm(prompt, model_key, api_keys)
    return results
