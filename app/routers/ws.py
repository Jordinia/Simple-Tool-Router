from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.agent import agentic_select_and_run

ws_router = APIRouter()

@ws_router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            # Use the same agentic routing as the /query endpoint
            result = await agentic_select_and_run(data)
            await ws.send_json({
                "query": result["query"],
                "tool_used": result["tool_used"],
                "result": result["result"]
            })
    except WebSocketDisconnect:
        pass
