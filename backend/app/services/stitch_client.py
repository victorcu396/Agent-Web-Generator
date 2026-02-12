import httpx
from app.dto.web_plan_dto import WebPlanDTO

STITCH_MCP_URL = "http://localhost:3001/generate"


async def generate_with_stitch(plan: WebPlanDTO) -> str:

    payload = {
        "type": plan.site_type,
        "sections": plan.sections,
        "style": plan.style,
    }

    # include optional assets
    if getattr(plan, 'images', None):
        payload['images'] = plan.images
    if getattr(plan, 'docs', None):
        payload['docs'] = plan.docs

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(STITCH_MCP_URL, json=payload)

    response.raise_for_status()

    data = response.json()

    return data["html"]
