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

# Configurar logging
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
_lock = asyncio.Lock()  # Evita condición de carrera en inicialización concurrente


async def _initialize():
    global _toolset, _runner, _session, _session_service
    async with _lock:
        if _runner is not None:
            return
    

    if _runner is not None:
        return

    _toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://stitch.googleapis.com/mcp",
            headers={
                "Accept": "application/json",
                "X-Goog-Api-Key": STITCH_API_KEY
            },
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT")
        ),
    )

    root_agent = Agent(
        name="stitch_agent",
        model="gemini-2.5-flash",
        instruction=(
        "You are a professional web UI generator powered by Google Stitch. "
        "Whenever the user asks for a webpage, you MUST generate full, valid HTML/CSS/JS code. "
        "Do NOT provide explanations or summaries. "
        "Respond only with code that can be used directly in a browser."
        ),
        tools=[_toolset],
    )
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
            ),
        )

        root_agent = Agent(
            name="stitch_agent",
            model="gemini-2.5-flash",
            instruction=(
                "You are a UI design assistant powered by Google Stitch. "
                "Generate complete, responsive HTML/CSS/JS pages based on the user's plan. "
                "Return only valid HTML code, no explanations."
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

    user_text = f"Genera una página {plan.site_type} con secciones {plan.sections} y estilo {plan.style}."
    if getattr(plan, 'images', None):
        user_text += f" Usa estas imágenes: {plan.images}."
    if getattr(plan, 'docs', None):
        user_text += f" Refiérete a estos documentos: {plan.docs}."

    logger.info(f"Generando página tipo '{plan.site_type}'...")

    content = types.Content(role="user", parts=[types.Part(text=user_text)])

    html_parts = []
    events = _runner.run_async(
        session_id=_session.id,
        user_id=_session.user_id,
        new_message=content
    )

    async for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            for p in event.content.parts:
                if getattr(p, "text", None):
                    html_parts.append(p.text)

    result = "\n".join(html_parts)
    logger.info(f"Página generada: {len(result)} caracteres")
    return result