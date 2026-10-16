from numpy import extract
from httpx2 import query
import uuid
from sqlalchemy.connectors import asyncio
import os
from typing import Annotated
from typing_extensions import TypedDict
import operator
import asyncio
import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START, END

from langgraph.checkpoint.postgres import PostgresSaver

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

# from tools.tavily_tool import tavily_search
from mcp_client import (
    tavily_mcp_search,
    aviation_mcp_call,
    get_airports,
    get_airlines,
    extract_destination,
    weather_mcp_search,
    forecast_mcp_search
)

# from tools.flight_tool import search_flights

from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",

)

DATABASE_URL = os.getenv("DATABASE_URL")

# print(f"Database: {DATABASE_URL}")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL environment variable is not set (check your .env file)")

# if DATABASE_URL:
#     conn = psycopg.connect(DATABASE_URL)
#     print("Database connected")
# else:
#     print("DATABASE_URL not found")

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int
    weather_results: str

# Flight Agent
# def flight_agent(state: TravelState):
#     query = state["user_query"]
#     flight_data = search_flights(query)


#     return {
#         "flight_results": flight_data,
#         "messages": [
#             AIMessage(content=f"Found the following flights:")
#         ],
#         "llm_calls": state.get("llm_calls", 0) + 1
#     }

FLIGHT_AGENT_PROMPT = """
        <role>You are an expert travel agent.</role>

        You are tasked with helping a user plan flights for their trip.

        Use the following tools to find the best flights for the user:

        User query: {query}

        Available Airports:
        {airport_data}

        Available Airlines:
        {airline_data}

Generate:

1. Likely departure airports
2. Likely destination airports
3. Likely airlines
4. Possible dates
5. Possible times
6. Possible prices
7. Typical flight duration
8. Peak season pricing warning
9. Booking advice

Return concise travel guidance.
        

"""

# Flight Agent
def flight_agent(state: TravelState):
    print("\nInside Flight Agent\n")

    query = state["user_query"]

    try:
        airports = asyncio.run(
            aviation_mcp_call(
                "list_airports",
            )
        )

        airlines = asyncio.run(
            aviation_mcp_call(
                "list_airlines",
            )
        )

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000],
        )
    
        response = llm.invoke(
            [
                SystemMessage(content="You are an expert travel agent. You are very good at planning flights."),
                HumanMessage(content=prompt)
            ]
        )

        flight_data = response.content

    except Exception as e:

        flight_data = f"Unable to fetch flight data: {str(e)}"


    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
    




        
# Hotel Agent
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    # hotel_results = tavily_search(query)

    hotel_results = asyncio.run(
        tavily_mcp_search(query)
    )

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content=f"Found the best hotels:")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# Weather Agent
def weather_agent(state: TravelState):

    city = extract_destination(state["user_query"])

    weather_data = asyncio.run(
        weather_mcp_search(city)
    )

    forecast_data = asyncio.run(
        forecast_mcp_search(city)
    )

    return {
        "weather_results": f"""
        Current weather for {city}:
        {weather_data}

        5-day forecast for {city}:
        {forecast_data}
        """,
        "messages": [
            AIMessage(
                content="Weather information fetched."
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

    

# Itinerary Agent
def itinerary_agent(state: TravelState):
   prompt = f"""
   Using the flight and hotel information below, create a travel itinerary.

   User query: {state['user_query']}

   Flight information: {state['flight_results']}

   Hotel information: {state['hotel_results']}

   Weather Information:
   {state['weather_results']}

   """
   response = llm.invoke([
    SystemMessage(
        content="You are an expert travel agent. You are very good at creating detailed travel itineraries."
    ),
    HumanMessage(content=prompt)
   ])
   return {
       "itinerary": response.content,
       "messages": [response],
       "llm_calls": state.get("llm_calls", 0) + 1
   }


# Final Agent
# def final_agent(state: TravelState):
#     final_prompt = f"""
#     Generate final travel response.

#     Flights: {state['flight_results']}
#     Hotels: {state['hotel_results']}
#     Itinerary: {state['itinerary']}
#     """

#     response = llm.invoke([
#         HumanMessage(content=final_prompt)
#     ])

#     return {
#         "messages": [response],
#         "llm_calls": state.get("llm_calls", 0) + 1
#     }


# Building the graph
graph = StateGraph(TravelState)  # pyright: ignore[reportArgumentType]

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)
# graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", END)
# graph.add_edge("final_agent", END)

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    prepare_threshold=0,
    row_factory=dict_row,
)


checkpointer = PostgresSaver(_conn)

checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)



if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    user_input = input("Enter travel request: ")

    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    print("\nFINAL RESPONSE:\n")

    for msg in result["messages"]:
        print(msg.content)