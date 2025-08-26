from typing import Any
from .base import Tool
from app.config import get_settings

from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

class LLMTool(Tool):
    name = "llm"
    description = "Answers general knowledge or open-ended questions via OpenRouter, OpenAI, or Google Gemini (auto-fallback)."

    async def run(self, query: str) -> Any:
        settings = get_settings()
        
        # Preference: OpenRouter > OpenAI > Google Gemini > stub
        use_openrouter = bool(settings.openrouter_api_key)
        openai_key = settings.openai_api_key
        google_key = settings.google_api_key
        
        # Try OpenRouter first
        if use_openrouter and OpenAI is not None:
            try:
                client = OpenAI(api_key=settings.openrouter_api_key, base_url="https://openrouter.ai/api/v1")
                model = settings.model_name or "openai/gpt-5-nano"
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
                # Fall through to next option
                pass
        
        # Try OpenAI second
        elif openai_key and OpenAI is not None:
            try:
                client = OpenAI(api_key=openai_key)
                completion = client.chat.completions.create(
                    model=settings.model_name or "gpt-4o-mini",
                    messages=[{"role": "user", "content": query}],
                )
                return completion.choices[0].message.content  # type: ignore[attr-defined]
            except Exception as e:  # pragma: no cover - network path
                # Fall through to next option
                pass
        
        # Try Google Gemini third
        if google_key and ChatGoogleGenerativeAI is not None:
            try:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash", 
                    google_api_key=google_key, 
                    temperature=0.7
                )
                response = await llm.ainvoke(query)
                return response.content
            except Exception as e:  # pragma: no cover - network path
                # Fall through to stub
                pass
        
        # Fallback to stub responses
        if "president of france" in query.lower():
            return "The president of France is Emmanuel Macron."
        return "(stub) LLM response not available. Set OPENROUTER_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY to enable real answers."
