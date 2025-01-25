import os
from typing import Dict, Any
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
BASE_URL = "https://app.ticketmaster.com/discovery/v2"

def fetch_events(keyword: str = None, city: str = None, start_date: str = None) -> Dict[str, Any]:
    """Fetch events from Ticketmaster API"""
    
    # Default to events in the next 30 days if no date provided
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "classificationName": "music",
        "size": 20,
        "startDateTime": f"{start_date}T00:00:00Z",
        "endDateTime": f"{end_date}T23:59:59Z"
    }
    
    if keyword:
        params["keyword"] = keyword
    if city:
        params["city"] = city
    
    try:
        response = requests.get(f"{BASE_URL}/events.json", params=params)
        response.raise_for_status()
        data = response.json()
        
        # Transform Ticketmaster data into our format
        events = []
        for event in data.get("_embedded", {}).get("events", []):
            event_data = {
                "id": event["id"],
                "artist": event["name"],
                "venue": event["_embedded"]["venues"][0]["name"],
                "date": event["dates"]["start"]["localDate"],
                "time": event["dates"]["start"].get("localTime", "20:00"),
                "available_tickets": []
            }
            
            # Extract pricing information if available
            if "priceRanges" in event:
                for i, price in enumerate(event["priceRanges"]):
                    ticket = {
                        "section": f"Section {i+1}",
                        "row": str(i+1),
                        "price": price["min"],
                        "quantity": 10  # Default quantity
                    }
                    event_data["available_tickets"].append(ticket)
            
            events.append(event_data)
        
        return {"events": events}
    
    except requests.RequestException as e:
        print(f"Error fetching events: {e}")
        # Return sample data as fallback
        return concert_tickets

# Sample fallback data
concert_tickets = {
    "events": [
        {
            "id": "1",
            "artist": "Taylor Swift",
            "venue": "Madison Square Garden",
            "date": "2025-03-15",
            "time": "20:00",
            "available_tickets": [
                {"section": "A1", "row": "1", "price": 350.00, "quantity": 4},
                {"section": "B2", "row": "5", "price": 250.00, "quantity": 8},
                {"section": "C3", "row": "10", "price": 150.00, "quantity": 12}
            ]
        },
        {
            "id": "2",
            "artist": "Ed Sheeran",
            "venue": "Barclays Center",
            "date": "2025-04-20",
            "time": "19:30",
            "available_tickets": [
                {"section": "Floor", "row": "2", "price": 300.00, "quantity": 6},
                {"section": "Lower Bowl", "row": "8", "price": 200.00, "quantity": 10},
                {"section": "Upper Bowl", "row": "15", "price": 100.00, "quantity": 15}
            ]
        }
    ]
}
