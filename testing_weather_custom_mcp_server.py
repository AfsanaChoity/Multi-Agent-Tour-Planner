
import os
import asyncio

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

client = MultiServerMCPClient(
    {
        "weather": {
            "transport": "stdio",  #for local mcp
            "command": r"C:\Users\User\Desktop\MULTI_AGENT_SYSTEM_FOR_TOUR_PLANING\aviationstack-mcp\.venv\Scripts\python.exe",
            "args": [
                r"C:\Users\User\Desktop\MULTI_AGENT_SYSTEM_FOR_TOUR_PLANING\custom_weather_mcp_server.py"
            ],
            "env": {
                "WEATHER_API_KEY": WEATHER_API_KEY
            }
        }

    }
)


import asyncio

async def main():

    tools = await client.get_tools()

    print("\nAvailable Weather Tools: \n")

    for tool in tools:
        print(f"{tool.name}")

asyncio.run(main())