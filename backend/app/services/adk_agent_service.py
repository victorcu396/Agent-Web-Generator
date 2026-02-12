import os
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

load_dotenv()

STITCH_API_KEY = os.getenv("STITCH_API_KEY")
APP_NAME = "stitch_chat_app"
USER_ID = "stitch_chat_user"


class ADKAgentService:
    def __init__(self):
        self.session_service = None
        self.session = None
        self.runner = None
        self.toolset = None
        self.initialized = False

    async def initialize(self):
        """Inicializa el agente y la sesión de forma asíncrona"""
        if self.initialized:
            return

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
                "You are a UI design assistant powered by Google Stitch. "
                "Help users create beautiful web designs for their projects. "
                "When users ask for designs, provide helpful suggestions and generate HTML/CSS code. "
                "Be friendly, helpful, and creative in your responses. "
                "Respond in the same language as the user."
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

    async def chat(self, user_message: str) -> str:
        """Envía un mensaje al agente y obtiene la respuesta"""
        await self.initialize()

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

        return "\n".join(response_parts) if response_parts else "No response from agent"

    async def close(self):
        """Cierra la conexión con el toolset"""
        if self.toolset:
            await self.toolset.close()
            self.initialized = False
