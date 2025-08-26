from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .query import select_tool

ws_router = APIRouter()

@ws_router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            tool = select_tool(data)
            result = await tool.run(data)
            await ws.send_json({
                "query": data,
                "tool_used": tool.name,
                "result": result,
            })
    except WebSocketDisconnect:
        pass
