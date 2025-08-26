from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .router import router, select_tool, NAME_TO_TOOL

app = FastAPI(
    title="Simple Tool Router", 
    version="0.1.0"
    )
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            # treat each message as a query
            tool = select_tool(data)
            result = await tool.run(data)
            await ws.send_json({
                "query": data,
                "tool_used": tool.name,
                "result": result,
            })
    except WebSocketDisconnect:
        pass

@app.exception_handler(Exception)
async def default_exception_handler(request, exc):  # type: ignore
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# For 'uvicorn app.main:app --reload'
__all__ = ["app"]
