from ticket_data import fetch_events, make_api_request
from pprint import pprint
import os
from dotenv import load_dotenv
import requests
import logging
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_key():
    """Test the Ticketmaster API key with detailed error reporting"""
    api_key = os.getenv("TICKETMASTER_API_KEY")
    if not api_key:
        logger.error("TICKETMASTER_API_KEY not found in environment variables")
        return False
    
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": api_key,
        "size": 1,
        "classificationName": "music",
        "countryCode": "US"
    }
    
    try:
        response = requests.get(url, params=params)
        status_code = response.status_code
        
        print(f"\nAPI Response Status Code: {status_code}")
        print("\nAPI Response Headers:")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        if status_code == 200:
            data = response.json()
            print("\nAPI Response Preview:")
            print(json.dumps(data, indent=2)[:500])
            return True
        elif status_code == 401:
            logger.error("Invalid API key")
            return False
        elif status_code == 429:
            logger.error("Rate limit exceeded")
            return False
        else:
            logger.error(f"Unexpected status code: {status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def test_search():
    """Test the event search functionality"""
    try:
        # Test with minimal parameters
        print("\nTesting basic event search...")
        events = fetch_events()
        
        if events['events']:
            print(f"Found {len(events['events'])} events")
            event = events['events'][0]
            print("\nFirst event details:")
            print(f"Artist: {event['artist']}")
            print(f"Venue: {event['venue']}")
            print(f"Date: {event['date']}")
            print(f"Time: {event['time']}")
            print("\nTicket Information:")
            for ticket in event['available_tickets']:
                print(f"Section: {ticket['section']}")
                print(f"Row: {ticket['row']}")
                print(f"Price: ${ticket['price']:.2f}")
                print(f"Quantity: {ticket['quantity']}")
                print("---")
        else:
            print("No events found in basic search")
        
        # Test with specific parameters
        print("\nTesting search with specific parameters...")
        specific_events = fetch_events(
            keyword="Concert",
            city="New York",
            start_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        if specific_events['events']:
            print(f"\nFound {len(specific_events['events'])} events with specific parameters")
            event = specific_events['events'][0]
            print("\nFirst event details:")
            print(f"Artist: {event['artist']}")
            print(f"Venue: {event['venue']}")
            print(f"Date: {event['date']}")
            print(f"Time: {event['time']}")
        else:
            print("No events found with specific parameters")
            
    except Exception as e:
        logger.error(f"Error during search test: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("Testing Ticketmaster API Integration")
    print("===================================")
    
    # Step 1: Test API key
    print("\nStep 1: Testing API Key")
    if not test_api_key():
        print("Failed to validate API key. Stopping tests.")
        return
    
    # Step 2: Test search functionality
    print("\nStep 2: Testing Search Functionality")
    if not test_search():
        print("Failed to test search functionality.")
        return
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    load_dotenv()
    main()
