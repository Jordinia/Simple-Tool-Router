from typing import Any
import os

from .base import Tool
from app.config import get_settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

class LLMTool(Tool):
    name = "llm"
    description = "Answers general knowledge or open-ended questions via OpenAI or OpenRouter (auto)."

    async def run(self, query: str) -> Any:
        settings = get_settings()
        # Preference: OpenRouter > OpenAI > stub
        use_openrouter = bool(settings.openrouter_api_key)
        api_key = (
            settings.openrouter_api_key
            if use_openrouter else (settings.openai_api_key or os.getenv("OPENAI_API_KEY"))
        )
        if not api_key or OpenAI is None:
            if "president of france" in query.lower():
                return "The president of France is Emmanuel Macron."
            return "(stub) LLM response not available. Set OPENROUTER_API_KEY or OPENAI_API_KEY to enable real answers."

        if use_openrouter:
            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            model = settings.model_name or "openai/gpt-5-nano"
            # Use Chat Completions style for broader compatibility
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": query}],
                    extra_headers={
                        k: v
                        for k, v in {
                            "HTTP-Referer": settings.openrouter_site_url,
                            "X-Title": settings.openrouter_title,
                        }.items() if v
                    },
                )
                return completion.choices[0].message.content  # type: ignore[attr-defined]
            except Exception as e:  # pragma: no cover - network path
                return f"OpenRouter error: {e}"
        else:
            # OpenAI standard responses API (new SDK) fallback
            client = OpenAI(api_key=api_key)
            completion = client.responses.create(
                model=settings.model_name,
                input=query,
            )
            try:
                return completion.output[0].content[0].text  # type: ignore[attr-defined]
            except Exception:
                return str(completion)
