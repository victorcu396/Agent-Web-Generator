from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from app.api.routes.generate import router as generate_router
from app.api.routes.chat import router as chat_router

app = FastAPI(title="AI Web Builder")

# Ensure uploads directory exists and serve it at /uploads
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(generate_router)
app.include_router(chat_router)
