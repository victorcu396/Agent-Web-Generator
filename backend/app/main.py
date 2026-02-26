import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.api.routes.generate import router as generate_router
from app.api.routes.chat import router as chat_router
from app.db.database import engine, test_connection
from app.db import models

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Web Builder")
upload_dir = os.path.join(os.path.dirname(__file__), "uploads") 
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)

app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
# Middlewares — siempre DESPUÉS de crear app
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

@app.middleware("http")
async def limit_upload_size(request, call_next):
    if request.method == "POST" and "/upload" in str(request.url):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 50 * 1024 * 1024:
            return JSONResponse({"error": "Archivo demasiado grande. Máximo 50MB."}, status_code=413)
    return await call_next(request)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

GENERATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generations'))
os.makedirs(GENERATIONS_DIR, exist_ok=True)
app.mount("/generations", StaticFiles(directory=GENERATIONS_DIR), name="generations")

app.include_router(generate_router)
app.include_router(chat_router)

@app.on_event("startup")
async def startup():
    if test_connection():
        models.Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas/verificadas correctamente")
    else:
        logger.error("No se pudo conectar a la BD al iniciar")