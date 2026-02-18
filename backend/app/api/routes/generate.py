from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from app.dto.prompt_dto import PromptDTO
from app.dto.result_dto import GeneratedPageDTO
from app.agents.web_builder_agent import WebBuilderAgent
import os
import uuid

router = APIRouter()
agent = WebBuilderAgent()

@router.post("/generate", response_model=GeneratedPageDTO)
async def generate_page(data: PromptDTO):
    result = await agent.run(data)
    return result

@router.post("/generate/upload", response_model=GeneratedPageDTO)
async def generate_with_upload(
    prompt: str = Form(...),
    images: List[UploadFile] = File(default=[]),
    docs: List[UploadFile] = File(default=[]),
):
    """Accepta archivos (imágenes y docs), los guarda en backend/uploads y llama al agente."""
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
    upload_dir = os.path.abspath(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)

    image_paths = []
    for f in images:
        filename = f"{uuid.uuid4().hex}_{f.filename}"
        dest = os.path.join(upload_dir, filename)
        with open(dest, "wb") as out:
            out.write(await f.read())
        image_paths.append(dest)

    doc_paths = []
    for f in docs:
        filename = f"{uuid.uuid4().hex}_{f.filename}"
        dest = os.path.join(upload_dir, filename)
        with open(dest, "wb") as out:
            out.write(await f.read())
        doc_paths.append(dest)

    prompt_dto = PromptDTO(prompt=prompt, images=image_paths, docs=doc_paths)
    result = await agent.run(prompt_dto)
    return result
