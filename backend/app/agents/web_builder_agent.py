from app.dto.prompt_dto import PromptDTO
from app.dto.web_plan_dto import WebPlanDTO
from app.dto.result_dto import GeneratedPageDTO
import asyncio
from app.services.page_generator import PageGenerator

class WebBuilderAgent:

    def __init__(self):
        self.generator = PageGenerator()

    def analyze_prompt(self, prompt: str, images: list | None = None, docs: list | None = None) -> WebPlanDTO:

        prompt_lower = prompt.lower()

        if "tienda" in prompt_lower or "shop" in prompt_lower:
            return WebPlanDTO(
                site_type="ecommerce",
                sections=["hero", "products", "pricing", "contact"],
                style="modern ecommerce",
                images=images,
                docs=docs,
            )

        if "portfolio" in prompt_lower:
            return WebPlanDTO(
                site_type="portfolio",
                sections=["hero", "projects", "about", "contact"],
                style="minimal modern",
                images=images,
                docs=docs,
            )

        return WebPlanDTO(
            site_type="ecommerce",
            sections=["hero", "products", "pricing", "contact"],
            style="modern ecommerce",
            prompt=prompt,  # ← añade esto en los tres returns
            images=images,
            docs=docs,
        )
        
    async def run(self, prompt_dto: PromptDTO) -> GeneratedPageDTO:

        plan = self.analyze_prompt(prompt_dto.prompt, images=getattr(prompt_dto, 'images', None), docs=getattr(prompt_dto, 'docs', None))

        html = await self.generator.generate(plan)

        return GeneratedPageDTO(
            html=html,
            framework="html"
        )
