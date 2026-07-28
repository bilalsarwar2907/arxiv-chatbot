import asyncio
from typing import List, Dict

from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import json


load_dotenv()

class MCP_ChatBot:
    def __init__(self):
        self.session: ClientSession = None
        self.sessions = []
        self.exit_stack = AsyncExitStack()
        self.available_tools: List[dict] = []
        self.tool_to_session = {}
        self.anthropic = Anthropic()

    async def process_query(self, query: str):
        """
        Temporary MCP test implementation.

        This bypasses the LLM and directly calls MCP tools
        so we can verify the client-server connection.
        """

        query = query.strip().lower()

        if query.startswith("search "):
            topic = query.replace("search ", "")

            result = await self.session.call_tool(
                "search_papers",
                arguments={
                    "topic": topic,
                    "max_results": 5,
                },
            )

            print("\nTool Result:")
            print(result)

        elif query.startswith("info "):
            paper_id = query.replace("info ", "")

            result = await self.session.call_tool(
                "extract_info",
                arguments={
                    "paper_id": paper_id,
                },
            )

            print("\nTool Result:")
            print(result)

        else:
            print(
                "\nCommands:\n"
                "search <topic>\n"
                "info <paper_id>\n"
                "quit"
            )

    async def chat_loop(self):
        print("\nMCP Chatbot Started!")
        print("Type 'quit' to exit.")

        while True:
            query = input("\nQuery: ").strip()

            if query.lower() == "quit":
                break

            await self.process_query(query)

    async def connect_to_server(self, server_name, server_config):
        try:
            server_params = StdioServerParameters(**server_config)

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            read, write = stdio_transport

            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            await session.initialize()

            self.sessions.append(session)

            response = await session.list_tools()

            print(
                f"\nConnected to {server_name} with tools:",
                [tool.name for tool in response.tools],
            )

            for tool in response.tools:
                self.tool_to_session[tool.name] = session

                self.available_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                )

        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)

            servers = data.get("mcpServers", {})

            for server_name, server_config in servers.items():
                await self.connect_to_server(
                    server_name,
                    server_config
                )

        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    bot = MCP_ChatBot()

    try:
        await bot.connect_to_servers()

        # set default session to first connected session if available
        if bot.sessions:
            bot.session = bot.sessions[0]

        await bot.chat_loop()
    finally:
        await bot.cleanup()
async def main():

   if __name__ == "__main__":
    asyncio.run(main())

        