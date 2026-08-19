"""
tools.py

This file contains the tool functions used by the chatbot.
"""

import json
import os
from typing import List

import arxiv

# Folder where paper information will be stored
PAPER_DIR = "papers"


def extract_info(paper_id: str) -> str:
    """Search for information about a specific paper across all topic directories."""
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)

        if os.path.isdir(item_path):
            topic_file_path = os.path.join(item_path, "papers_info.json")

            if os.path.isfile(topic_file_path):
                try:
                    with open(topic_file_path, "r", encoding="utf-8") as json_file:
                        saved_papers_info = json.load(json_file)

                    if paper_id in saved_papers_info:
                        return json.dumps(saved_papers_info[paper_id], indent=2)

                except (FileNotFoundError, json.JSONDecodeError):
                    continue

    return f"There's no saved information related to paper {paper_id}."


def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """Search for papers on arXiv based on a topic and store their information.

    Args:
        topic (str): Topic to search for.
        max_results (int): Maximum number of papers to return.

    Returns:
        List of paper IDs.
    """

    if not topic or not topic.strip():
        return []

    client = arxiv.Client()

    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = list(client.results(search))

    path = os.path.join(
        PAPER_DIR,
        topic.lower().replace(" ", "_"),
    )

    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "papers_info.json")

    papers_info = {}
    paper_ids = []

    for paper in papers:
        paper_id = paper.get_short_id()
        paper_ids.append(paper_id)

        papers_info[paper_id] = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }

    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(papers_info, json_file, indent=2)

    print(f"Results are saved in: {file_path}")

    return paper_ids


# Tool Definitions
tools = [
    {
        "name": "search_papers",
        "description": (
            "Search for papers on arXiv based on a topic and store their information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to search for"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to retrieve",
                    "default": 5
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "extract_info",
        "description": (
            "Search for information about a specific paper"
            " across all topic directories."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {
                    "type": "string",
                    "description": "The ID of the paper to look for"
                }
            },
            "required": ["paper_id"]
        }
    }
]
mapping_tool_function = {
    "search_papers": search_papers,
    "extract_info": extract_info,
}

def execute_tool(tool_name, tool_args):
    # I-003: guard against unknown tool names
    if tool_name not in mapping_tool_function:
        return (
            f"Error: unknown tool '{tool_name}'. "
            f"Available tools: {list(mapping_tool_function.keys())}"
        )

    # I-003: guard against bad arguments or runtime errors in the tool itself
    try:
        result = mapping_tool_function[tool_name](**tool_args)
    except TypeError as e:
        return f"Error: invalid arguments for tool '{tool_name}': {e}"
    except Exception as e:
        return f"Error executing tool '{tool_name}': {e}"

    if result is None:
        result = "The operation completed but didn't return any results."
    elif isinstance(result, list):
        result = ", ".join(result)
    elif isinstance(result, dict):
        result = json.dumps(result, indent=2)
    else:
        result = str(result)

    return result
