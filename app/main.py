from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routers import router, ws_router

app = FastAPI(
    title="Simple Tool Router", 
    version="0.1.0"
    )
app.include_router(router)
app.include_router(ws_router)

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def default_exception_handler(request, exc):  # type: ignore
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# For 'uvicorn app.main:app --reload'
__all__ = ["app"]
