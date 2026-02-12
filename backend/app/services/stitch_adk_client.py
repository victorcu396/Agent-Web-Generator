import os
import asyncio
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

async def generate_with_adk(plan) -> str:
    toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://stitch.googleapis.com/mcp",
            headers={"Accept": "application/json", "X-Goog-Api-Key": STITCH_API_KEY},
        ),
    )

    root_agent = Agent(
        name="stitch_agent",
        model="gemini-2.5-flash",
        instruction="You are a UI design assistant...",
        tools=[toolset],
    )

    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)

    runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)

    # Construir prompt desde `plan`
    user_text = f"Genera una página {plan.site_type} con secciones {plan.sections} y estilo {plan.style}"
    content = types.Content(role="user", parts=[types.Part(text=user_text)])

    events = runner.run_async(session_id=session.id, user_id=session.user_id, new_message=content)

    html_parts = []
    async for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            for p in event.content.parts:
                if getattr(p, "text", None):
                    html_parts.append(p.text)

    await toolset.close()
    return "\n".join(html_parts)