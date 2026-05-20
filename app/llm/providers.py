import json
import re

from app.core.config import get_settings


_JSON_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def call_llm(prompt: str) -> str:
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()

    if provider == "groq":
        return _call_groq(prompt)

    if provider == "gemini":
        return _call_gemini(prompt)

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def _call_groq(prompt: str) -> str:
    from groq import Groq

    settings = get_settings()

    if not settings.groq_api_key:
        raise ValueError(
        "GROQ_API_KEY is required when LLM_PROVIDER=groq. "
        "To run without an external LLM key, set LLM_PROVIDER=mock."
    )

    client = Groq(api_key=settings.groq_api_key)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate strict JSON only. "
                    "Do not include markdown fences, commentary, or extra text."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=1200,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Groq returned an empty response.")

    return _clean_json_text(content)


def _call_gemini(prompt: str) -> str:
    from google import genai

    settings = get_settings()

    if not settings.gemini_api_key:
        raise ValueError(
        "GEMINI_API_KEY is required when LLM_PROVIDER=gemini. "
        "To run without an external LLM key, set LLM_PROVIDER=mock."
    )

    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return _clean_json_text(response.text)


def _clean_json_text(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = _JSON_FENCE_PATTERN.sub("", cleaned).strip()

    # Validate early so downstream parser receives reliable JSON text.
    json.loads(cleaned)

    return cleaned