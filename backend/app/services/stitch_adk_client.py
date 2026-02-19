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
                project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            ),
        )

        root_agent = Agent(
            name="stitch_agent",
            model="gemini-2.5-flash",
            instruction=(
                "You are a professional web UI generator powered by Google Stitch. "
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


async def generate_with_adk(plan) -> str:
    await _initialize()

    user_text = (
        f"Generate a complete {plan.site_type} HTML page with sections: {plan.sections} and style: {plan.style}. "
        f"Return ONLY the raw HTML code starting with <!DOCTYPE html>. "
        f"Do not describe it, do not summarize it, just return the complete HTML."
    )
    if getattr(plan, 'images', None):
        user_text += f" Include these images: {plan.images}."
    if getattr(plan, 'docs', None):
        user_text += f" Reference these documents: {plan.docs}."

    logger.info(f"Generando página tipo '{plan.site_type}'...")

    # Sesión fresca por cada generación para evitar historial acumulado
    session = await _session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID
    )

    content = types.Content(role="user", parts=[types.Part(text=user_text)])

    html_parts = []
    async for event in _runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for p in event.content.parts:
                if getattr(p, "text", None):
                    html_parts.append(p.text)

    result = "\n".join(html_parts)
    logger.info(f"Página generada: {len(result)} caracteres")
    return result