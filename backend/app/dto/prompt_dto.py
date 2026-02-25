from pydantic import BaseModel
from typing import List

class PromptDTO(BaseModel):
    prompt: str
    images: List[str] = []
    docs: List[str] = []
    customization: Optional[WebCustomizationDTO] = None
    """Personalización opcional. Si se omite, el agente decide todo automáticamente."""
