import os
import asyncio
import logging
import base64
import httpx
from pathlib import Path
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
# URL pública del servidor — usada para construir las URLs de las imágenes en el HTML
# En desarrollo: http://localhost:8000 | En producción: https://tudominio.com
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")

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
            ),
        )

        root_agent = Agent(
            name="stitch_agent",
            model="gemini-2.5-flash",
            instruction=(
                "You are a professional web UI generator powered by Google Stitch. "
                "Generate complete, responsive HTML/CSS/JS pages based on the user's plan. "
                "ALWAYS return the complete raw HTML/CSS/JS code directly. "
                "NEVER describe what you generated. "
                "NEVER summarize. "
                "NEVER say 'I have generated' or 'The page has been created'. "
                "Your response must start with <!DOCTYPE html> and end with </html>. "
                "When the user provides image URLs, you MUST use them as <img src='...'> "
                "in the appropriate sections of the page. NEVER replace them with placeholders. "
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


def _build_public_image_urls(image_paths: list) -> list[str]:
    """
    Convierte rutas absolutas del servidor en URLs públicas accesibles desde el navegador.
    Ejemplo: /home/app/uploads/abc123_foto.jpg → http://localhost:8000/uploads/abc123_foto.jpg
    """
    urls = []
    for path in image_paths:
        filename = Path(path).name
        urls.append(f"{BASE_URL}/uploads/{filename}")
    return urls


async def generate_with_adk(plan) -> str:
    await _initialize()

    parts = []
    image_paths = getattr(plan, 'images', None) or []

    # --- Añadir imágenes como base64 para que Gemini las vea visualmente ---
    for image_path in image_paths:
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            ext = Path(image_path).suffix.lower().replace('.', '')
            mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
            parts.append(types.Part(
                inline_data=types.Blob(
                    mime_type=mime,
                    data=image_data
                )
            ))
            logger.info(f"Imagen añadida como base64: {image_path}")
        except Exception as e:
            logger.warning(f"No se pudo cargar imagen {image_path}: {e}")

    # --- Construir texto del prompt ---
    user_text = (
        f"Generate a complete {plan.site_type} HTML page "
        f"with sections: {plan.sections} and style: {plan.style}. "
        f"User request: {getattr(plan, 'prompt', '')}. "
    )

    # Clave: incluir las URLs públicas en el prompt para que el HTML generado
    # las use directamente en los atributos src de las imágenes
    if image_paths:
        public_urls = _build_public_image_urls(image_paths)
        logger.info(f"URLs públicas de imágenes: {public_urls}")
        user_text += (
            f"IMPORTANT: The user has uploaded {len(public_urls)} image(s). "
            f"You MUST use these exact URLs as <img src='...'> in the HTML, "
            f"placed in the most relevant sections (hero, gallery, products, etc). "
            f"Do NOT use placeholder images. The image URLs are: {public_urls}. "
        )

    if getattr(plan, 'docs', None):
        user_text += f"Reference these documents for content: {plan.docs}. "

    user_text += "Return ONLY the raw HTML code starting with <!DOCTYPE html>."

    parts.append(types.Part(text=user_text))

    logger.info(f"Generando página tipo '{plan.site_type}' con {len(image_paths)} imágenes...")

    # Sesión fresca por cada generación
    session = await _session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    content = types.Content(role="user", parts=parts)

    html_parts = []
    download_url = None

    async for event in _runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=content
    ):
        logger.info(f"EVENT: {event}")

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