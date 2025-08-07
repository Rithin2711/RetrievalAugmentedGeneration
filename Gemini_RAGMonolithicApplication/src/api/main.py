from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the built frontend (React, built to ../static/)
static_path = os.path.join(os.path.dirname(__file__), '..', 'static')
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/api/health")
def health_check():
    """PUBLIC_INTERFACE
    Returns basic health check for service.
    """
    return {"message": "Healthy"}


@app.get("/", response_class=HTMLResponse)
async def serve_react_index(request: Request):
    """PUBLIC_INTERFACE
    Serves the React frontend (index.html for SPA fallback).
    """
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse(
        "<h1>Gemini-RAG Frontend not yet built.<br/>Please run 'npm run build' in /src/frontend.</h1>", status_code=503
    )

# Catch-all for client-side routing (React Router)
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_react_app_catchall(full_path: str):
    """PUBLIC_INTERFACE
    SPA Fallback route for React client-side navigation.
    """
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse(
        "<h1>Gemini-RAG Frontend not yet built.<br/>Please run 'npm run build' in /src/frontend.</h1>", status_code=503
    )
