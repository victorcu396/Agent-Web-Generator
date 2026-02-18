from app.services.stitch_adk_client import generate_with_adk

class PageGenerator:
    async def generate(self, plan):
        return await generate_with_adk(plan)