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
# Get Response
# ============================================================

def get_response(user_message: str) -> str:
    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": user_message,
            }
        ],
        tools=tools,
    )

    message = response.choices[0].message

    # Normal response
    if not getattr(message, "tool_calls", None):
        return message.content

    # Tool call
    tool_call = message.tool_calls[0]

    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    result = execute_tool(tool_name, tool_args)

    return result


# ============================================================
# Chat Loop
# ============================================================

def chat_loop():
    while True:
        user_message = input("\nYou: ")

        if user_message.lower() == "quit":
            print("Goodbye!")
            break

        response = get_response(user_message)

        print("\nAssistant:")
        print(response)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    chat_loop()
