from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import transcribe, sessions, export

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",       # Swagger UI available at /docs during dev
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sessions.router,   prefix=settings.API_PREFIX, tags=["Sessions"])
app.include_router(transcribe.router, prefix=settings.API_PREFIX, tags=["Transcription"])
app.include_router(export.router,     prefix=settings.API_PREFIX, tags=["Export"])


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.VERSION}
