from tools import execute_tool

result = execute_tool(
    "search_papers",
    {
        "topic": "machine learning",
        "max_results": 3
    }
)

print(result)