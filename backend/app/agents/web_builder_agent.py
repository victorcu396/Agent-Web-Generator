from app.dto.prompt_dto import PromptDTO
from app.dto.web_plan_dto import WebPlanDTO
from app.dto.result_dto import GeneratedPageDTO
from app.services.page_generator import PageGenerator

# Separa logica de las posibles entradas, para que sea más facil reescalado
SITE_TYPE_KEYWORDS: dict[str, tuple[str, list[str], str]] = {
    "ecommerce": (
        ["tienda", "shop", "store", "ecommerce", "compra", "producto"],
        ["hero", "products", "pricing", "contact"],
        "modern ecommerce",
    ),
    "portfolio": (
        ["portfolio", "portafolio", "proyectos", "trabajos", "cv"],
        ["hero", "projects", "about", "contact"],
        "minimal modern",
    )
}

DEFAULT_PLAN = ("landing", ["hero", "features", "pricing", "contact"], "modern saas")


class WebBuilderAgent:

    def __init__(self):
        self.generator = PageGenerator()

    def analyze_prompt(
        self,
        prompt: str,
        images: list[str] | None = None,
        docs: list[str] | None = None,
    ) -> WebPlanDTO:
        """
        Determina el tipo de sitio a partir de keywords en el prompt.
        Posible mejora de datos a añadir para mejorar el prompt
        """
        prompt_lower = prompt.lower()

        for site_type, (keywords, sections, style) in SITE_TYPE_KEYWORDS.items():
            if any(kw in prompt_lower for kw in keywords):
                return WebPlanDTO(
                    site_type=site_type,
                    sections=sections,
                    style=style,
                    images=images,
                    docs=docs,
                )

        site_type, sections, style = DEFAULT_PLAN
        return WebPlanDTO(
            site_type=site_type,
            sections=sections,
            style=style,
            images=images,
            docs=docs,
        )

    async def run(self, prompt_dto: PromptDTO) -> GeneratedPageDTO:
        """
        Genera la página HTML basado en el prompt usando PageGenerator.
        """
        plan = self.analyze_prompt(
            prompt_dto.prompt,
            images=prompt_dto.images or None,
            docs=prompt_dto.docs or None,
        )

        html = await self.generator.generate(plan)

        return GeneratedPageDTO(html=html, framework="html")