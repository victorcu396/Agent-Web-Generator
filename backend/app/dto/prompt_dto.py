from pydantic import BaseModel
from typing import List

class PromptDTO(BaseModel):
    prompt: str
    images: List[str] = []
    docs: List[str] = []
