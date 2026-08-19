import asyncio
from typing import List

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


class MCP_ChatBot:
    def __init__(self):
        self.session: ClientSession = None
        self.available_tools: List[dict] = []

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

    async def connect_to_server_and_run(self):
        server_params = StdioServerParameters(
            command="python",
            args=["research_server.py"],
            env=None,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session

                await session.initialize()

                response = await session.list_tools()

                print(
                    "\nConnected to server with tools:",
                    [tool.name for tool in response.tools],
                )

                self.available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]

                await self.chat_loop()


async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()


if __name__ == "__main__":
    asyncio.run(main())
