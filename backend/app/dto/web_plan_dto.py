from pydantic import BaseModel
from typing import List, Optional

class WebPlanDTO(BaseModel):
    site_type: str
    sections: List[str]
    style: str
    prompt: Optional[str] = None  
    images: Optional[List[str]] = None
    docs: Optional[List[str]] = None
