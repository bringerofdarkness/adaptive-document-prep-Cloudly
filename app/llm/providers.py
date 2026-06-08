import json
import logging
from typing import List

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def call_llm(prompt: str) -> str:
    """
    Executes LLM generation with fallback circuit breaking capabilities.
    Attempts the primary provider from configuration first. If it encounters a
    persistent failure, it routes sequentially through the alternative backup paths.
    """
    settings = get_settings()
    primary_provider = settings.llm_provider.lower().strip()

    provider_sequence: List[str] = [primary_provider]
    for backup in ["groq", "gemini", "mock"]:
        if backup not in provider_sequence:
            provider_sequence.append(backup)

    last_exception = None

    for provider in provider_sequence:
        try:
            if provider == "groq":
                return _call_groq_with_retry(prompt)
            if provider == "gemini":
                return _call_gemini_with_retry(prompt)
            if provider == "mock":
                return _call_mock_fallback(prompt)
        except Exception as exc:
            last_exception = exc
            logger.warning(
                f"[CIRCUIT BREAKER] Provider '{provider}' failed execution. "
                f"Exception details: {exc}. Attempting next available fallback strategy..."
            )

    raise RuntimeError(
        f"All configured LLM providers and fallbacks failed execution sequences. Last error: {last_exception}"
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=6),
    retry=retry_if_exception_type((ValueError, Exception)),
    reraise=True,
)
def _call_groq_with_retry(prompt: str) -> str:
    from groq import Groq

    settings = get_settings()

    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is absent.")

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
        raise ValueError("Groq returned an empty response string.")

    return _clean_json_text(content)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=6),
    retry=retry_if_exception_type((ValueError, Exception)),
    reraise=True,
)
def _call_gemini_with_retry(prompt: str) -> str:
    from google import genai

    settings = get_settings()

    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is absent.")

    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response string.")

    return _clean_json_text(response.text)


def _call_mock_fallback(prompt: str) -> str:
    """
    Dynamic mock fallback interface execution path.
    Instead of hardcoding structures, this intercepts execution and routes directly 
    to your existing codebase's local generation utility function.
    """
    logger.info("[CIRCUIT BREAKER] Triggering dynamic local mock fallback generator.")
    

    from app.llm.mcq_generator import get_mock_provider_response
    return get_mock_provider_response(prompt)


def _clean_json_text(raw_text: str) -> str:
    """
    Cleans markdown code blocks using runtime character code lookups
    to completely prevent IDE copy-paste line break formatting errors.
    """
    cleaned = raw_text.strip()
    
    # Generate the backtick delimiter string dynamically using ASCII value 96
    fence_char = chr(96)
    fence_marker = fence_char + fence_char + fence_char
    
    # Strip leading markers
    if cleaned.startswith(fence_marker):
        cleaned = cleaned[3:]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
            
    # Strip trailing markers
    if cleaned.endswith(fence_marker):
        cleaned = cleaned[:-3]
        
    cleaned = cleaned.strip()
    
    # Validate final JSON structural integrity
    json.loads(cleaned)
    return cleaned