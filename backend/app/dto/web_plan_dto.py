from pydantic import BaseModel
from typing import List, Optional

class WebPlanDTO(BaseModel):
    site_type: str
    sections: List[str]
    style: str
    images: Optional[List[str]] = None
    docs: Optional[List[str]] = None
