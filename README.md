# Simple-Tool-Router

Lightweight FastAPI + (optional) LangChain service that routes natural language queries to purpose‑built tools via a small agentic router.

Current built‑in tools:

- **weather**: live current weather via OpenWeatherMap (stub fallback)
- **math**: safe evaluation of arithmetic / bitwise expressions (AST sandboxed)
- **llm**: general knowledge / open‑ended answers with multi‑provider fallback options

Routing Strategy:
1. If `GOOGLE_API_KEY` is set a fast Gemini model (gemini-2.0-flash) produces structured JSON (`{"tool": ..., "input": ...}`) deciding which tool to call (no chain-of-thought; only selection & argument extraction).
2. If agent or API key unavailable, simple keyword heuristics choose the tool.

Provider Fallback for `llm` tool (in order): OpenRouter → OpenAI → Google Gemini → deterministic stub.

WebSocket endpoint returns one JSON object per message. The REST `/query` endpoint streams a single newline‑delimited JSON object (NDJSON style) for easy incremental consumption.

### Design
- One lightweight LLM (Gemini) decides which tool to call.
- Weather / Math: only routing LLM call + direct underlying tool run (total 1 LLM call).
- General queries: routing decides "llm" then we call the LLM tool (2 LLM calls total: routing + answer). If routing falls back to heuristics (no Gemini key) only the answer LLM call (or stub) is performed.

## Features

- Agentic structured tool selection (Pydantic output parsing) when Gemini available
- Heuristic fallback (no external keys required to try it)
- Safe math execution (AST whitelist)
- Tool abstraction for easy extension
- Streaming REST `/query` endpoint (NDJSON line)
- `/ws` WebSocket (request → single JSON response)
- Graceful stub responses when API keys absent
- Docker image with health check

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment (.env file)

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
${EDITOR:-nano} .env
```

Alternatively export variables directly (overrides .env):
```bash
export OPENWEATHER_API_KEY=your_openweather_key
export OPENAI_API_KEY=your_open_ai_key
export MODEL_NAME=gpt-4o-mini
export GOOGLE_API_KEY=your_google_gemini_key
export OPENROUTER_API_KEY=your_openrouter_key
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Server listens by default on `http://127.0.0.1:8000`.

### 4. Send requests

`POST /query` (returns a single JSON object streamed as one line)
```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is 42 * 7?"}' | jq
```
### Sample Queries & Expected Outputs

#### Math
Request:
```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is 42 * 7?"}'
```
Expected output:
```json
{
  "query": "What is 42 * 7?",
  "tool_used": "math",
  "result": "294"
}
```

#### Weather
Request (city extracted by agent):
```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What's the weather like today in Paris?"}' | jq
```
Expected outputs:
```jsonc
// Live (example)
{
  "query": "What's the weather like today in Paris?",
  "tool_used": "weather",
  "result": "It's 26°C and scattered clouds in Paris, FR."
}
// Stub (no API key / network issue)
{
  "query": "What's the weather like today in Paris?",
  "tool_used": "weather",
  "result": "I don't have access to weather data right now, but you asked about Paris."
}
```

#### LLM
Request:
```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "Who is the president of France?"}' | jq
```
Expected outputs:
```jsonc
// With real provider
{
  "query": "Who is the president of France?",
  "tool_used": "llm",
  "result": "The president of France is Emmanuel Macron." 
}
// Stub fallback
{
  "query": "Who is the president of France?",
  "tool_used": "llm",
  "result": "The president of France is Emmanuel Macron." 
}
```

### WebSocket

```bash
python - <<'PY'
import asyncio, websockets, json
async def main():
    uri = 'ws://127.0.0.1:8000/ws'
    async with websockets.connect(uri) as ws:
        for q in [
            'What is 5 + 8 * 2?',
            'What\u2019s the weather like today in Paris?',
            'Tell me a fun fact about space.'
        ]:
            await ws.send(q)
            print(await ws.recv())
asyncio.run(main())
PY
```

### Health Check
`GET /health` -> `{ "status": "ok, made by Jordinia" }`

### Run Tests
```bash
pytest -q
```
All test files live in `tests/` (agent routing, math, weather). 20+ tests cover routing heuristics, agent fallback, safety, and tool behavior.

## Docker (Optional)

Build and run:
```bash
docker build -t simple-tool-router .
docker run -p 8000:8000 --env OPENWEATHER_API_KEY=xxx --env OPENAI_API_KEY=yyy simple-tool-router
```

## Environment Variables

| Name | Purpose | Default |
|------|---------|---------|
| OPENWEATHER_API_KEY | Live weather lookups (stub if unset) | — |
| OPENAI_API_KEY | OpenAI LLM provider (2nd fallback) | — |
| OPENROUTER_API_KEY | OpenRouter provider (1st fallback) | — |
| OPENROUTER_SITE_URL | (Optional) Referer header for OpenRouter | — |
| OPENROUTER_TITLE | (Optional) Title header for OpenRouter | — |
| GOOGLE_API_KEY | Enables Gemini router + final LLM fallback | — |
| MODEL_NAME | Preferred OpenAI/OpenRouter model | gpt-4o-mini |
| WEATHER_DEFAULT_CITY | Fallback city for empty weather input | San Francisco |
| WEATHER_UNITS | 'metric' (°C) or 'imperial' (°F) | metric |

## Math Tool Security

The math tool parses expressions with Python `ast.parse` and *only* allows a strict whitelist of node types (`_ALLOWED_NODES`) and operators (`_OPERATORS`). No names, attributes, calls, or comprehensions are permitted, preventing code execution (e.g. `__import__('os')`). Multiplication variants (`x`, `×`, `∗`) are normalized to `*` before parsing. If any disallowed node appears the evaluation aborts.

Supported operators: `+ - * / // % ** << >> | & ^` and unary `+ -`.

This approach provides deterministic, safe arithmetic without `eval`.

## Tech Stack
- FastAPI
- LangChain (agent routing & Gemini model)
- OpenAI SDK
- Google Generative AI
- Requests (weather) / asyncio
- Pytest

## Project Structure

```
Simple-Tool-Router/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py                # FastAPI app entry
│   ├── models/
│   │   ├── __init__.py
│   │   └── query_models.py    # Pydantic request/response models
│   ├── routers/
│   │   ├── __init__.py        # exports router + ws_router
│   │   ├── query.py           # /query endpoint (streaming JSON line)
│   │   └── ws.py              # /ws WebSocket endpoint (per-message JSON)
│   ├── agent.py               # Agentic routing (Gemini)
│   └── tools/
│       ├── __init__.py (optional)
│       ├── base.py            # Tool abstract base
│       ├── llm_tool.py
│       ├── math_tool.py
│       └── weather_tool.py
├── tests/
│   ├── test_agent.py
│   ├── test_math_tool.py
│   └── test_weather_tool.py
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
└── requirements.txt
```