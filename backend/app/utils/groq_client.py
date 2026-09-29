"""
AidFlow AI - Groq Client Utility
Wraps Groq API calls with retry logic and structured output parsing.
"""

from groq import Groq
from functools import lru_cache
from app.config import get_settings
import json
import time


@lru_cache()
def get_groq_client() -> Groq:
    """Create and return a cached Groq client instance."""
    settings = get_settings()
    return Groq(api_key=settings.GROQ_API_KEY)


def call_groq(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    json_mode: bool = True,
    retries: int = 2,
) -> dict | str:
    """
    Make a Groq API call with retry logic.
    
    Args:
        system_prompt: System instruction for the model
        user_prompt: User message content
        temperature: Creativity parameter (0.0-1.0)
        max_tokens: Max output tokens
        json_mode: If True, parse response as JSON
        retries: Number of retry attempts on failure
    
    Returns:
        Parsed JSON dict if json_mode, else raw string
    """
    settings = get_settings()
    client = get_groq_client()

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_mode else None,
            )

            content = response.choices[0].message.content

            if json_mode:
                return json.loads(content)
            return content

        except json.JSONDecodeError:
            if attempt < retries:
                continue
            # Return raw content on final attempt
            return {"raw_response": content, "parse_error": True}

        except Exception as e:
            if attempt < retries:
                # Exponential backoff
                time.sleep(2 ** attempt)
                continue
            raise e
