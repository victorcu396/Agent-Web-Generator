from fastapi import FastAPI
from app.api.routes.generate import router as generate_router
from app.api.routes.chat import router as chat_router

app = FastAPI(title="AI Web Builder")

app.include_router(generate_router)
app.include_router(chat_router)
