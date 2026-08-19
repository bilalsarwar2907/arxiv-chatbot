import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import tools, execute_tool

# ============================================================
# Load Environment Variables
# ============================================================

load_dotenv()

# ============================================================
# OpenRouter Client
# ============================================================

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# ============================================================
# Convert tools to OpenAI format
# tools.py uses Anthropic format (input_schema); OpenAI expects
# {"type": "function", "function": {"name", "description", "parameters"}}
# ============================================================

openai_tools = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
        },
    }
    for t in tools
]

# ============================================================
# Get Response
# ============================================================


def get_response(messages: list) -> str:
    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
        max_tokens=1024,
        messages=messages,
        tools=openai_tools,
    )

    message = response.choices[0].message

    # No tool call — plain text response
    if response.choices[0].finish_reason != "tool_calls":
        return message.content

    # Tool call — execute and send result back to Claude
    messages.append({
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ],
    })

    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        result = execute_tool(tool_name, tool_args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    # Second call — Claude summarises the tool result
    follow_up = client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
        max_tokens=1024,
        messages=messages,
        tools=openai_tools,
    )
    return follow_up.choices[0].message.content


# ============================================================
# Chat Loop
# ============================================================

def chat_loop():
    messages = []

    while True:
        user_message = input("\nYou: ")

        if user_message.lower() == "quit":
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_message})
        response = get_response(messages)
        messages.append({"role": "assistant", "content": response})

        print("\nAssistant:")
        print(response)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    chat_loop()
