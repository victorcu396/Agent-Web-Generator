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
APP_NAME = "stitch_app"
USER_ID = "stitch_user"

# Instancia única reutilizable
_toolset = None
_runner = None
_session = None
_session_service = None

async def _initialize():
    global _toolset, _runner, _session, _session_service

    if _runner is not None:
        return

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


async def generate_with_adk(plan) -> str:
    await _initialize()  # ← conecta a Stitch MCP (solo la primera vez)

    user_text = f"Genera una página {plan.site_type} con secciones {plan.sections} y estilo {plan.style}."
    if getattr(plan, 'images', None):
        user_text += f" Usa estas imágenes: {plan.images}."
    if getattr(plan, 'docs', None):
        user_text += f" Refiérete a estos documentos: {plan.docs}."

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

    return "\n".join(html_parts)