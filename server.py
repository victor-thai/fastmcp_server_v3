from fastmcp import FastMCP, Client
from typing import Any, Optional, List, Dict
import datetime
import json
import asana
import os

# Initialize the FastMCP server
mcp = FastMCP("AsanaTaskManager")

@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"

@mcp.tool
def test_function(name: str) -> str:
    return f"I like fantasy football"

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)