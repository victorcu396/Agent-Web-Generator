import os
import asyncio
import logging
import httpx
from pathlib import Path
from dotenv import load_dotenv

# SDK y ADK imports
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
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")

APP_NAME = "stitch_app"
USER_ID = "stitch_user"

_toolset = None
_runner = None
_session_service = None
_lock = asyncio.Lock()


async def _initialize():
    global _toolset, _runner, _session_service

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
                "You are a professional web UI generator powered by Google Stitch. "
                "When the user asks for a page, ALWAYS: "
                "1. Call create_project to create a new project. "
                "2. Call generate_screen_from_text with the project ID. "
                "3. Return the COMPLETE raw HTML code directly in your response. "
                "NEVER give a download link. NEVER describe the result. "
                "NEVER say 'you can download'. NEVER include explanatory text. "
                "Your ENTIRE response must be ONLY the HTML code starting with <!DOCTYPE html> and ending with </html>. "
                "If you have a download URL, fetch its content and return the HTML directly."
                "- Respond in the same language the user writes in. "
            ),
            tools=[_toolset],
        )

        _session_service = InMemorySessionService()

        _runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=_session_service
        )

        logger.info("Stitch ADK client inicializado correctamente")


def _build_public_image_urls(image_paths: list) -> list[str]:
    urls = []
    for path in image_paths:
        filename = Path(path).name
        urls.append(f"{BASE_URL}/uploads/{filename}")
    return urls


async def generate_with_adk(plan) -> str:
    await _initialize()

    parts = []
    image_paths = getattr(plan, 'images', None) or []

    # Añadir imágenes como bytes
    for image_path in image_paths:
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            ext = Path(image_path).suffix.lower().replace('.', '')
            mime = f"image/{'jpeg' if ext == 'jpg' else ext}"

            parts.append(types.Part.from_bytes(
                data=image_data,
                mime_type=mime
            ))

        except Exception as e:
            logger.warning(f"No se pudo cargar imagen {image_path}: {e}")

    # Prompt
    user_text = f"Generate a complete {plan.site_type} HTML page."

    if image_paths:
        public_urls = _build_public_image_urls(image_paths)
        user_text += f" Use these images: {public_urls}"

    parts.append(types.Part.from_text(text=user_text))

    session = await _session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID
    )

    content = types.Content(role="user", parts=parts)

    html_parts = []
    download_url = None

    async for event in _runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=content
    ):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for p in event.content.parts:
                if hasattr(p, 'function_response') and p.function_response:
                    result = p.function_response.response
                    if isinstance(result, dict):
                        for key in ['url', 'download_url', 'file_url', 'link']:
                            if key in result:
                                download_url = result[key]

        if event.is_final_response() and event.content:
            for p in event.content.parts:
                if getattr(p, "text", None):
                    html_parts.append(p.text)

    if download_url:
        logger.info(f"Descargando HTML desde: {download_url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(download_url)

            if response.status_code == 200:
                result = response.text
                logger.info("Descarga exitosa")
                return result
    result = "\n".join(html_parts)
    logger.info(f"Página generada: {len(result)} caracteres")
    return result

