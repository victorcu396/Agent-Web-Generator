from pydantic import BaseModel
from typing import List, Optional, Literal

# Secciones disponibles que el cliente puede elegir
SectionType = Literal[
    "hero",
    "about",
    "products",
    "pricing",
    "contact",
    "faq",
    "testimonials",
    "gallery",
    "blog",
    "team",
    "projects",
]

ColorScheme = Literal["light", "dark", "auto"]


class WebCustomizationDTO(BaseModel):
    sections: Optional[List[SectionType]] = None
    """Si se envía, el agente usará exactamente estas secciones en el orden indicado.
    Si es None, Gemini decide las secciones según el tipo de sitio detectado."""

    style: Optional[str] = None
    """Descripción libre del estilo deseado. Ej: 'minimal', 'bold', 'corporate', 'playful'."""

    color_scheme: Optional[ColorScheme] = None
    """Esquema de color general de la página."""

    primary_color: Optional[str] = None
    """Color primario en formato hex. Ej: '#3B82F6'."""

    font_style: Optional[str] = None
    """Estilo tipográfico. Ej: 'modern', 'serif', 'playful', 'monospace'."""

    language: Optional[str] = "es"
    """Idioma del contenido generado. Ej: 'es', 'en', 'fr'."""