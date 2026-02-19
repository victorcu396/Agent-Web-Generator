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

# Carga variables de entorno al importar
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

STITCH_API_KEY = os.getenv("STITCH_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
APP_NAME = "stitch_chat_app"
USER_ID = "stitch_chat_user"


class ADKAgentService:
    """
    Servicio de chat interactivo con el agente ADK/Stitch.
    Mantiene sesiones para conversaciones multi-turno.
    Basado en agent_principal.py pero sin modo interactivo (para web).
    """
    def __init__(self):
        self.session_service = None
        self.session = None
        self.runner = None
        self.toolset = None
        self.initialized = False
        self._lock = asyncio.Lock()  # Evita condición de carrera en inicialización concurrente

    async def initialize(self):
        """Inicializa el agente y la sesión de forma asíncrona"""
        async with self._lock:
            if self.initialized:
                return

            logger.info("Inicializando ADKAgentService...")

            self.toolset = McpToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url="https://stitch.googleapis.com/mcp",
                    headers={
                        "Accept": "application/json",
                        "X-Goog-Api-Key": STITCH_API_KEY,
                    },
                ),
            )

            root_agent = Agent(
                name="stitch_chat_agent",
                model="gemini-2.5-flash",
                instruction=(
                    "You are a professional web UI generator powered by Google Stitch. "
                    "Whenever the user asks for a webpage, you MUST generate full, valid HTML/CSS/JS code. "
                    "Do NOT provide explanations or summaries. "
                    "Respond only with code that can be used directly in a browser."
                ),
                tools=[self.toolset],
            )

            self.session_service = InMemorySessionService()
            self.session = await self.session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
            )

            self.runner = Runner(
                app_name=APP_NAME,
                agent=root_agent,
                session_service=self.session_service,
            )

            self.initialized = True
            logger.info("ADKAgentService inicializado correctamente")

    async def chat(self, user_message: str) -> str:
        """Envía un mensaje al agente y obtiene la respuesta"""
        await self.initialize()

        logger.info(f"Mensaje recibido: {user_message[:50]}")

        user_message = f"GENERATE_HTML: {user_message}"

        content = types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        )

        response_parts = []
        events = self.runner.run_async(
            session_id=self.session.id,
            user_id=self.session.user_id,
            new_message=content,
        )

        async for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_parts.append(part.text)

        result = "\n".join(response_parts) if response_parts else "No response from agent"
        logger.info(f"Respuesta generada: {len(result)} caracteres")
        return result

    async def close(self):
        """Cierra la conexión con el toolset"""
        if self.toolset:
            await self.toolset.close()
            self.initialized = False
            logger.info("ADKAgentService cerrado")