import os
import asyncio
import logging
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

STITCH_API_KEY = os.getenv("STITCH_API_KEY")
APP_NAME = "stitch_app"
USER_ID = "stitch_user"

_toolset = None
_runner = None
_session = None
_session_service = None
_lock = asyncio.Lock()


async def _initialize():
    global _toolset, _runner, _session, _session_service

    async with _lock:
        if _runner is not None:
            return

        logger.info("Inicializando Stitch ADK client...")

        _toolset = McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="https://stitch.googleapis.com/mcp",
                headers={
                    "Accept": "application/json",
                    "X-Goog-Api-Key": STITCH_API_KEY
                },
                # project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            ),
        )

        root_agent = Agent(
            name="stitch_agent",
            model="gemini-2.0-flash",
            instruction=(
                "You are a professional web UI generator powered by Google Stitch. "
                "Generate complete, responsive HTML/CSS/JS pages based on the user's plan. "
                "ALWAYS return the complete raw HTML/CSS/JS code directly. "
                "NEVER describe what you generated. "
                "NEVER summarize. "
                "NEVER say 'I have generated' or 'The page has been created'. "
                "Your response must start with <!DOCTYPE html> and end with </html>. "
                "Return ONLY the HTML code, nothing else."
            ),
            tools=[_toolset],
        )

        _session_service = InMemorySessionService()
        _session = await _session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID
        )

        _runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=_session_service
        )

        logger.info("Stitch ADK client inicializado correctamente")


import httpx

async def generate_with_adk(plan) -> str:
    await _initialize()

    user_text = (
        f"Generate a complete {plan.site_type} HTML page with sections: {plan.sections} and style: {plan.style}. "
        f"User request: {getattr(plan, 'prompt', '')}. "
        f"Return ONLY the raw HTML code starting with <!DOCTYPE html>."
    )
    if getattr(plan, 'images', None):
        user_text += f" Include these images: {plan.images}."
    if getattr(plan, 'docs', None):
        user_text += f" Reference these documents: {plan.docs}."

    session = await _session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    content = types.Content(role="user", parts=[types.Part(text=user_text)])

    html_parts = []
    download_url = None

    async for event in _runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=content
    ):
        logger.info(f"EVENT: {event}")  # para ver qué devuelve

        # Busca URL de descarga en tool results
        if hasattr(event, 'content') and event.content:
            for p in event.content.parts:
                if hasattr(p, 'function_response') and p.function_response:
                    result = p.function_response.response
                    logger.info(f"TOOL RESULT: {result}")
                    if isinstance(result, dict):
                        for key in ['url', 'download_url', 'file_url', 'link']:
                            if key in result:
                                download_url = result[key]

        if event.is_final_response() and event.content and event.content.parts:
            for p in event.content.parts:
                if getattr(p, "text", None):
                    html_parts.append(p.text)

    # Si encontró URL de descarga, descarga el HTML
    if download_url:
        logger.info(f"Descargando HTML desde: {download_url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url)
            if response.status_code == 200:
                return response.text

    result = "\n".join(html_parts)
    logger.info(f"Página generada: {len(result)} caracteres")
    return result