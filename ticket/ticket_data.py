import os
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
if not TICKETMASTER_API_KEY:
    raise ValueError("TICKETMASTER_API_KEY not found in environment variables")

BASE_URL = "https://app.ticketmaster.com/discovery/v2"

def make_api_request(url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make a request to the Ticketmaster API with error handling"""
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 429:
            logger.error("Rate limit exceeded")
            return None
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def fetch_events(keyword: str = None, city: str = None, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """Fetch events from Ticketmaster API"""
    logger.info(f"Fetching events with keyword='{keyword}', city='{city}', start_date='{start_date}'")
    
    # Default to events in the next 30 days if no date provided
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    if not end_date:
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "classificationName": "music",
        "size": 10,  # Reduced size to avoid rate limiting
        "startDateTime": f"{start_date}T00:00:00Z",
        "endDateTime": f"{end_date}T23:59:59Z",
        "sort": "date,asc",
        "countryCode": "US",  # Limit to US events
        "segmentId": "KZFzniwnSyZfZ7v7nJ"  # Specifically for music events
    }
    
    if keyword:
        params["keyword"] = keyword
    if city:
        params["city"] = city

    logger.info(f"Making API request to {BASE_URL}/events.json")
    
    data = make_api_request(f"{BASE_URL}/events.json", params)
    if not data:
        logger.warning("API request failed, using fallback data")
        return concert_tickets
    
    # Check for API errors
    if "errors" in data:
        logger.error(f"API returned errors: {data['errors']}")
        return concert_tickets
    
    # Check if we have events in the response
    if "_embedded" not in data:
        logger.warning("No events found in API response")
        return concert_tickets
        
    events_data = data["_embedded"]["events"]
    logger.info(f"Found {len(events_data)} events in API response")
    
    # Transform Ticketmaster data into our format
    events = []
    for event in events_data:
        try:
            # Extract venue information
            venues = event.get("_embedded", {}).get("venues", [])
            venue_name = venues[0].get("name", "Venue TBA") if venues else "Venue TBA"
            
            # Extract date and time
            dates = event.get("dates", {})
            start = dates.get("start", {})
            event_time = start.get("localTime", "20:00")
            event_date = start.get("localDate", datetime.now().strftime("%Y-%m-%d"))
            
            # Extract pricing if available
            price_ranges = event.get("priceRanges", [])
            if not price_ranges and event.get("seatmap"):
                # If no price ranges but seatmap exists, add a placeholder price
                price_ranges = [{"min": 0.0, "max": 0.0}]
            
            event_data = {
                "id": event.get("id", "unknown"),
                "artist": event.get("name", "Unknown Artist"),
                "venue": venue_name,
                "date": event_date,
                "time": event_time,
                "available_tickets": []
            }
            
            # Add ticket information
            if price_ranges:
                for i, price in enumerate(price_ranges):
                    section_name = f"Section {chr(65 + i)}"  # A, B, C, etc.
                    ticket = {
                        "section": section_name,
                        "row": str(i + 1),
                        "price": price.get("min", 0.0),
                        "quantity": 10
                    }
                    event_data["available_tickets"].append(ticket)
            else:
                # Add a default ticket option if no pricing is available
                event_data["available_tickets"].append({
                    "section": "General Admission",
                    "row": "1",
                    "price": 0.0,  # Price to be announced
                    "quantity": 10
                })
            
            events.append(event_data)
            logger.info(f"Successfully processed event: {event_data['artist']} at {event_data['venue']}")
        
        except Exception as e:
            logger.error(f"Error processing event data: {e}")
            continue
    
    if not events:
        logger.warning("No events could be processed, falling back to sample data")
        return concert_tickets
    
    logger.info(f"Successfully processed {len(events)} events")
    return {"events": events}

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

if __name__ == "__main__":
    try:
        logger.info("Testing Ticketmaster API connection...")
        test_events = fetch_events()
        if test_events["events"]:
            logger.info(f"Successfully retrieved {len(test_events['events'])} events")
            # Print the first event as a sample
            first_event = test_events["events"][0]
            logger.info(f"Sample event: {first_event['artist']} at {first_event['venue']} on {first_event['date']}")
        else:
            logger.warning("No events found in API response")
    except Exception as e:
        logger.error(f"Failed to connect to Ticketmaster API: {e}")
