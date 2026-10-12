import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

def search_flights(query):
    url = "https://api.aviationstack.com/v1/flights"
    params = {
        "access_key": API_KEY,
        "limit" : 5,
    }

    response = requests.get(url,params=params)

    data = response.json()

    flights = []

    if 'data' in data:

        for flight in data['data'][:5]:

            airline = flight.get("airline",{}).get("name", "Unknown Airline")

            departure = flight.get("departure",{}).get("airport", "Unknown Departure")

            arrival = flight.get("arrival",{}).get("airport", "Unknown Arrival")

            status = flight.get("flight_status", "Unknown Status")

            flights.append(f"Airline: {airline}, Departure: {departure}, Arrival: {arrival}, Status: {status}")
    
    return '\n'.join(flights)

            



    
