import os
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
        self.available_resources: List = []
        self.available_prompts: List = []
        self.tool_to_session = {}
        self.resource_to_session = {}
        self.anthropic = Anthropic(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api",
        )

    async def process_query(self, query: str):
        messages = [{"role": "user", "content": query}]
        response = self.anthropic.messages.create(
            model="anthropic/claude-opus-4-5",
            max_tokens=1024,
            tools=self.available_tools,
            messages=messages,
        )

        while response.stop_reason == "tool_use":
            tool_use = next(b for b in response.content if b.type == "tool_use")
            tool_name = tool_use.name
            tool_args = tool_use.input

            session = self.tool_to_session.get(tool_name)
            result = await session.call_tool(tool_name, arguments=tool_args)

            messages = [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response.content},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": result.content,
                        }
                    ],
                },
            ]

            response = self.anthropic.messages.create(
                model="anthropic/claude-opus-4-5",
                max_tokens=1024,
                tools=self.available_tools,
                messages=messages,
            )

        final_response = next(
            (b.text for b in response.content if hasattr(b, "text")), None
        )
        print(f"\nResponse: {final_response}")

    async def list_prompts(self):
        print("\nAvailable Prompts:")
        if not self.available_prompts:
            print("No prompts available.")
            return
        for prompt in self.available_prompts:
            print(f"- {prompt.name}: {prompt.description}")
            if prompt.arguments:
                for arg in prompt.arguments:
                    print(f"    {arg.name} (required: {arg.required})")

    async def get_resource(self, query):
        topic = query[1:]  # strip the @
        uri = "papers://folders" if topic == "folders" else f"papers://{topic}"

        # find a session that can serve this resource
        session = self.resource_to_session.get(uri)
        if not session:
            # fall back: any session that has paper resources
            for key, s in self.resource_to_session.items():
                if key.startswith("papers://"):
                    session = s
                    break

        if not session:
            print(f"\nNo resource found for: {query}")
            return

        try:
            result = await session.read_resource(uri)
            print(f"\nResource [{uri}]:")
            for content in result.contents:
                if hasattr(content, "text"):
                    print(content.text)
        except Exception as e:
            print(f"\nError reading resource: {e}")

    async def execute_prompt(self, query):
        # format: /prompt <name> [key=value ...]
        parts = query.strip().split()
        if len(parts) < 2:
            print("Usage: /prompt <name> [arg1=value1] [arg2=value2]")
            return

        prompt_name = parts[1]
        args = {}
        for part in parts[2:]:
            if "=" in part:
                key, value = part.split("=", 1)
                args[key] = value

        # find a session that has this prompt
        session = None
        for s in self.sessions:
            session = s
            break

        if not session:
            print(f"\nNo session available.")
            return

        try:
            result = await session.get_prompt(prompt_name, arguments=args)
            prompt_content = " ".join(
                msg.content.text if hasattr(msg.content, "text") else str(msg.content)
                for msg in result.messages
            )
            print(f"\nExecuting prompt: {prompt_name}")
            await self.process_query(prompt_content)
        except Exception as e:
            print(f"\nError executing prompt: {e}")

    async def chat_loop(self):
        print("\nMCP Chatbot Started!")
        print("Type 'quit' to exit.")
        print("Commands: /prompts | /prompt <name> [args] | @folders | @<topic>")

        while True:
            query = input("\nQuery: ").strip()

            if query.lower() == "quit":
                break
            elif query == "/prompts":
                await self.list_prompts()
            elif query.startswith("/prompt "):
                await self.execute_prompt(query)
            elif query.startswith("@"):
                await self.get_resource(query)
            else:
                await self.process_query(query)

    async def connect_to_server(self, server_name: str, server_config: dict):
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

            try:
                resources = await session.list_resources()
                for resource in resources.resources:
                    self.available_resources.append(resource)
                    self.resource_to_session[str(resource.uri)] = session
            except Exception:
                pass

            try:
                prompts = await session.list_prompts()
                for prompt in prompts.prompts:
                    self.available_prompts.append(prompt)
            except Exception:
                pass

        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            servers = data.get("mcpServers", {})
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    bot = MCP_ChatBot()
    try:
        await bot.connect_to_servers()
        if bot.sessions:
            bot.session = bot.sessions[0]
        await bot.chat_loop()
    finally:
        await bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
    