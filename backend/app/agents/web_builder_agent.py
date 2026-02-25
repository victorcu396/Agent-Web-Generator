from app.dto.prompt_dto import PromptDTO
from app.dto.web_plan_dto import WebPlanDTO
from app.dto.result_dto import GeneratedPageDTO
from app.dto.customization_dto import WebCustomizationDTO
import asyncio
import logging
from app.services.page_generator import PageGenerator

logger = logging.getLogger(__name__)


# Mapa de detección de tipo de sitio por palabras clave
SITE_TYPE_KEYWORDS = {
    "ecommerce": ["tienda", "shop", "store", "ecommerce", "venta", "compra", "producto"],
    "portfolio":  ["portfolio", "portafolio", "proyectos", "projects", "cv", "curriculum"],
    "landing":    ["landing", "presentación", "presentacion", "promocion", "promoción", "campaña"],
    "blog":       ["blog", "artículo", "articulo", "noticias", "news", "posts"],
    "corporate":  ["empresa", "company", "corporativo", "corporate", "negocio", "business"],
    "restaurant": ["restaurante", "restaurant", "menu", "menú", "comida", "food"],
}

# Secciones y estilos por defecto para cada tipo de sitio
SITE_DEFAULTS = {
    "ecommerce": {
        "sections": ["hero", "products", "pricing", "contact"],
        "style": "modern ecommerce",
    },
    "portfolio": {
        "sections": ["hero", "projects", "about", "contact"],
        "style": "minimal modern",
    },
    "landing": {
        "sections": ["hero", "about", "pricing", "testimonials", "contact"],
        "style": "bold landing",
    },
    "blog": {
        "sections": ["hero", "blog", "about", "contact"],
        "style": "clean editorial",
    },
    "corporate": {
        "sections": ["hero", "about", "team", "contact"],
        "style": "professional corporate",
    },
    "restaurant": {
        "sections": ["hero", "about", "gallery", "contact"],
        "style": "elegant restaurant",
    },
    # fallback genérico
    "generic": {
        "sections": ["hero", "about", "contact"],
        "style": "modern clean",
    },
}


class WebBuilderAgent:

    def __init__(self):
        self.generator = PageGenerator()

    # ------------------------------------------------------------------
    # Detección del tipo de sitio a partir del texto del prompt
    # ------------------------------------------------------------------
    def _detect_site_type(self, prompt_lower: str) -> str:
        for site_type, keywords in SITE_TYPE_KEYWORDS.items():
            if any(kw in prompt_lower for kw in keywords):
                return site_type
        return "generic"

    # ------------------------------------------------------------------
    # Construcción del plan base (misma lógica que antes, ampliada)
    # ------------------------------------------------------------------
    def _build_base_plan(
        self,
        prompt: str,
        images: list | None,
        docs: list | None,
    ) -> WebPlanDTO:
        site_type = self._detect_site_type(prompt.lower())
        defaults = SITE_DEFAULTS[site_type]

        return WebPlanDTO(
            site_type=site_type,
            sections=list(defaults["sections"]),  # copia para no mutar el dict
            style=defaults["style"],
            prompt=prompt,
            images=images,
            docs=docs,
        )

    # ------------------------------------------------------------------
    # Aplica las personalizaciones del cliente sobre el plan base
    # ------------------------------------------------------------------
    def _apply_customization(
        self,
        plan: WebPlanDTO,
        customization: WebCustomizationDTO | None,
    ) -> WebPlanDTO:
        if not customization:
            return plan

        # El cliente puede sobreescribir las secciones
        if customization.sections:
            plan.sections = list(customization.sections)
            logger.info(f"Secciones personalizadas: {plan.sections}")

        # El cliente puede sobreescribir el estilo
        if customization.style:
            plan.style = customization.style
            logger.info(f"Estilo personalizado: {plan.style}")

        # Color scheme, primary color y font se concatenan al estilo
        # para que el generador los reciba como contexto de diseño
        style_extras = []
        if customization.color_scheme:
            style_extras.append(f"color-scheme:{customization.color_scheme}")
        if customization.primary_color:
            style_extras.append(f"primary-color:{customization.primary_color}")
        if customization.font_style:
            style_extras.append(f"font:{customization.font_style}")
        if customization.language:
            style_extras.append(f"language:{customization.language}")

        if style_extras:
            plan.style = f"{plan.style} | {' '.join(style_extras)}"

        return plan

    # ------------------------------------------------------------------
    # Método público: analiza prompt + customization y devuelve el plan
    # (mantiene la firma anterior para no romper generate.py)
    # ------------------------------------------------------------------
    def analyze_prompt(
        self,
        prompt: str,
        images: list | None = None,
        docs: list | None = None,
        customization: WebCustomizationDTO | None = None,
    ) -> WebPlanDTO:
        plan = self._build_base_plan(prompt, images, docs)
        plan = self._apply_customization(plan, customization)
        logger.info(
            f"Plan generado → tipo: {plan.site_type} | "
            f"secciones: {plan.sections} | estilo: {plan.style}"
        )
        return plan

    # ------------------------------------------------------------------
    # Método principal: recibe el DTO completo y devuelve el HTML
    # ------------------------------------------------------------------
    async def run(self, prompt_dto: PromptDTO) -> GeneratedPageDTO:
        plan = self.analyze_prompt(
            prompt=prompt_dto.prompt,
            images=getattr(prompt_dto, "images", None),
            docs=getattr(prompt_dto, "docs", None),
            customization=getattr(prompt_dto, "customization", None),
        )

        html = await self.generator.generate(plan)

        return GeneratedPageDTO(
            html=html,
            framework="html",
        )