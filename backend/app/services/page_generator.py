import os
from dotenv import load_dotenv
from app.services.stitch_client import generate_with_stitch
from app.services.stitch_adk_client import generate_with_adk

load_dotenv()

class PageGenerator:
    async def generate(self, plan):
        if os.getenv("USE_ADK", "false").lower() == "true":
            return await generate_with_adk(plan)
        return await generate_with_stitch(plan)