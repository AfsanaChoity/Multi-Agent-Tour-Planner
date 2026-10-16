
import os
import asyncio

from typing import Any
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

connections: dict[str, Any] = {
    "tavily": {
        "transport": "streamable_http",  # for remote mcp
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",
    },
    "aviationstack": {
        "transport": "stdio",  # for local mcp
        "command": r"C:\Users\User\Desktop\MULTI_AGENT_SYSTEM_FOR_TOUR_PLANING\aviationstack-mcp\.venv\Scripts\python.exe",
        "args": [
            "-m",
            "aviationstack_mcp",
            "mcp",
            "run",
        ],
        "env": {
            "AVIATIONSTACK_API_KEY": AVIATIONSTACK_API_KEY,
        },
    },

    # Custom MCP Server
    "weather": {
            "transport": "stdio",  #for local mcp
            "command": r"C:\Users\User\Desktop\MULTI_AGENT_SYSTEM_FOR_TOUR_PLANING\aviationstack-mcp\.venv\Scripts\python.exe",
            "args": [
                r"C:\Users\User\Desktop\MULTI_AGENT_SYSTEM_FOR_TOUR_PLANING\custom_weather_mcp_server.py"
            ],
            "env": {
                "WEATHER_API_KEY": WEATHER_API_KEY
            }
    },
}

client = MultiServerMCPClient(connections)

# tools discovery
# async def main():

#     tools = await client.get_tools()

#     print("\n Available mcp:\n")

#     for t in tools:
#         print(f"{t.name}")

search_tool: Any = None
aviation_tools = {}

async def initialize_mcp():
    global search_tool
    global aviation_tools

    if search_tool is not None and aviation_tools:
        return

    tools = await client.get_tools()

    print("\nAvailable MCP tools:")

    for tool in tools:
        print(f"{tool.name}")
    
    search_tool = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"
    )

    aviation_tools = {
        tool.name: tool
        for tool in tools
        if tool.name != "tavily_search"

    }







# Tavily mcp search
async def tavily_mcp_search(query: str):
    await initialize_mcp()

    if search_tool is None:
        raise RuntimeError("tavily_search tool not found in MCP server tools.")

    result = await search_tool.ainvoke(
        {
            "query": query
        }
    )

    return result



# Aviation mcp search
async def aviation_mcp_call(tool_name: str, tool_args: dict = None):
    

    tools = await client.get_tools()

    tool = next(
        t for t in tools
        if t.name == tool_name
    )
   
    result = await tool.ainvoke(
        tool_args or {}
    )

    return result



# aviation mcp search for airports
async def get_airports():

    await initialize_mcp()

    tool = aviation_tools.get("list_airports")

    if not tool:
        return "Airport tool unavialable"

    result = await tool.ainvoke({})

    return result

    
# aviation mcp search for airlines
async def get_airlines():

    await initialize_mcp()

    tool = aviation_tools.get("list_airlines")

    if not tool:
        return "Airport tool unavialable"

    result = await tool.ainvoke({})

    return result
    
weather_tool = None
forecast_tool = None

#Weather mcp search
async def initialize_weather_tools():

    global weather_tool, forecast_tool

    if weather_tool is not None:
        return

    tools = await client.get_tools()

    weather_tool = next(
        t for t in tools
        if t.name == "get_weather"
    )

    forecast_tool = next(
        t for t in tools
        if t.name == "get_forecast"
    )


async def weather_mcp_search(city: str):
     await initialize_weather_tools()

     return await weather_tool.ainvoke({"city": city})

async def forecast_mcp_search(city: str):
    await initialize_weather_tools()

    return await forecast_tool.ainvoke({"city": city})


# Extract city
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-120b"
)

def extract_destination(query: str):

    prompt = f"""
    Extract the destination city or country from this user query:
    {query}

    Return ONLY the name of the destination, nothing else.
    """

    response = llm.invoke(prompt)
    
    city = response.content.strip()
    
    return city
    
# if __name__ == "__main__":
#     asyncio.run(main())