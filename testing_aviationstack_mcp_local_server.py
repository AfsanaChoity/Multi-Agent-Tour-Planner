
import os
import asyncio

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

client = MultiServerMCPClient(
    {
        "aviationstack": {
            "transport": "stdio",  #for local mcp
            "command": r"C:\Users\User\Desktop\MULTI_AGENT_SYSTEM_FOR_TOUR_PLANING\aviationstack-mcp\.venv\Scripts\python.exe",
            "args": [
                "-m",
                "aviationstack_mcp",
                "mcp",
                "run"
            ],
            "env": {
                "AVIATIONSTACK_API_KEY": AVIATIONSTACK_API_KEY
            }
        }

    }
)


import asyncio

async def main():

    tools = await client.get_tools()

    print("\n Available Tools: \n")

    for tool in tools:
        print(f"{tool.name}")

asyncio.run(main())