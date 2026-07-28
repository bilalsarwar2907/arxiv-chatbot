#!/usr/bin/env python3
"""
MCP Research Server

This module implements an MCP (Model Context Protocol) server that provides
two tools for interacting with arXiv papers:
    1. search_papers  – query arXiv, store results locally.
    2. extract_info   – retrieve stored information for a given paper ID.

The server uses FastMCP and communicates via stdio.
"""

import json
import os
from typing import List

import arxiv
from mcp.server.fastmcp import FastMCP

# ============================================================================
#  Constants
# ============================================================================

PAPER_DIR = "papers"  # Root directory where all paper data is stored

# ============================================================================
#  MCP Server Initialisation
# ============================================================================

mcp = FastMCP("research")

# ============================================================================
#  Tool 1: Search for Papers on arXiv
# ============================================================================

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.

    The function performs a query against arXiv, retrieves the specified
    number of results, and saves the metadata (title, authors, summary,
    PDF URL, publication date) into a JSON file under a directory named
    after the sanitised topic.

    Args:
        topic (str): The search topic / query string.
        max_results (int, optional): Maximum number of papers to return.
                                     Defaults to 5.

    Returns:
        List[str]: A list of arXiv paper IDs (short IDs) that were saved.
                   Returns an empty list if the topic is invalid.
    """
    # --------------------------------------------------------------------
    #  Input validation
    # --------------------------------------------------------------------
    if not topic or not topic.strip():
        return []  # No query → nothing to search

    # --------------------------------------------------------------------
    #  Perform the arXiv search
    # --------------------------------------------------------------------
    client = arxiv.Client()
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    papers = list(client.results(search))

    # --------------------------------------------------------------------
    #  Prepare the storage directory
    # --------------------------------------------------------------------
    # Sanitise the topic to create a safe folder name
    folder_name = topic.lower().replace(" ", "_")
    storage_path = os.path.join(PAPER_DIR, folder_name)
    os.makedirs(storage_path, exist_ok=True)

    # Path to the JSON file that will hold all paper information
    json_file_path = os.path.join(storage_path, "papers_info.json")

    # --------------------------------------------------------------------
    #  Extract metadata and save to JSON
    # --------------------------------------------------------------------
    papers_info = {}   # Maps paper_id -> metadata dict
    paper_ids = []     # List of paper IDs in the order they were returned

    for paper in papers:
        paper_id = paper.get_short_id()  # e.g. "2101.12345"
        paper_ids.append(paper_id)

        papers_info[paper_id] = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }

    # Write the collected data to the JSON file
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(papers_info, json_file, indent=2)

    # Inform the user (visible in server logs) where the data was saved
    print(f"Results are saved in: {json_file_path}")

    return paper_ids


# ============================================================================
#  Tool 2: Retrieve Information for a Specific Paper
# ============================================================================

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.

    The function scans every subdirectory under PAPER_DIR, looks for a
    'papers_info.json' file, and attempts to locate the given paper ID.
    If found, the corresponding metadata is returned as a JSON string.

    Args:
        paper_id (str): The arXiv ID of the paper (short format, e.g. "2101.12345").

    Returns:
        str: A JSON string containing the paper's metadata if found,
             otherwise an error message.
    """
    # Iterate over each topic directory inside the main papers folder
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)

        # Only consider directories (skip any stray files)
        if os.path.isdir(item_path):
            topic_file_path = os.path.join(item_path, "papers_info.json")

            # If the directory contains the expected JSON file, attempt to load it
            if os.path.isfile(topic_file_path):
                try:
                    with open(topic_file_path, "r", encoding="utf-8") as json_file:
                        papers_info = json.load(json_file)

                    # Check if the requested paper_id exists in this topic's data
                    if paper_id in papers_info:
                        # Return the paper's metadata as a pretty‑printed JSON string
                        return json.dumps(papers_info[paper_id], indent=2)

                except (FileNotFoundError, json.JSONDecodeError):
                    # If the file is missing or corrupted, skip this directory
                    continue

    # If we've gone through all directories and found nothing
    return f"There's no saved information related to paper {paper_id}."


# ============================================================================
#  Server Entry Point
# ============================================================================

if __name__ == "__main__":
    # Start the MCP server using stdio transport (the default for MCP)
    mcp.run(transport="stdio")