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

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
STITCH_API_KEY = os.getenv("STITCH_API_KEY")

APP_NAME = "stitch_app"
USER_ID = "stitch_user"


async def get_agent_and_toolset():
	"""Creates an ADK Agent equipped with tools from the Stitch MCP Server."""
	toolset = McpToolset(
		connection_params=StreamableHTTPConnectionParams(
			url="https://stitch.googleapis.com/mcp",
			headers={
				"Accept": "application/json",
				"X-Goog-Api-Key": STITCH_API_KEY,
			},
		),
	)

	root_agent = Agent(
		name="stitch_agent",
		description="An agent that generates UI designs using Google Stitch",
		model="gemini-2.5-flash",
		instruction=(
			"You are a UI design assistant powered by Google Stitch. "
			"Use the Stitch MCP tools to generate UI designs for mobile and web applications. "
			"When the user asks for a design, use the available tools to create it."
		),
		tools=[toolset],
	)
	return root_agent, toolset


async def chat():
	"""Interactive chat loop with the Stitch agent."""
	session_service = InMemorySessionService()
	session = await session_service.create_session(
		app_name=APP_NAME,
		user_id=USER_ID,
	)

	root_agent, toolset = await get_agent_and_toolset()

	runner = Runner(
		app_name=APP_NAME,
		agent=root_agent,
		session_service=session_service,
	)

	print("=" * 50)
	print("  Stitch UI Design Agent - Interactive Chat")
	print("  Type 'exit' or 'quit' to end the conversation")
	print("=" * 50)

	try:
		while True:
			query = input("\nYou: ").strip()
			if not query:
				continue
			if query.lower() in ("exit", "quit"):
				break

			content = types.Content(role="user", parts=[types.Part(text=query)])

			events_async = runner.run_async(
				session_id=session.id,
				user_id=session.user_id,
				new_message=content,
			)

			print("\nAgent: ", end="")
			async for event in events_async:
				if event.is_final_response():
					if event.content and event.content.parts:
						for part in event.content.parts:
							if hasattr(part, "text") and part.text:
								print(part.text)
	except KeyboardInterrupt:
		print("\n\nInterrupted by user.")
	finally:
		await toolset.close()
		print("Stitch MCP connection closed.")


if __name__ == "__main__":
	asyncio.run(chat())