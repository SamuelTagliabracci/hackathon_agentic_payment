from ticket_data import fetch_events
from pprint import pprint

def test_api():
    print("Testing Ticketmaster API...")
    
    # Test 1: Get all events
    print("\n1. Fetching all upcoming events:")
    events = fetch_events()
    print(f"Found {len(events['events'])} events")
    if events['events']:
        print("\nFirst event details:")
        pprint(events['events'][0])
    
    # Test 2: Search for specific artist
    print("\n2. Searching for 'Taylor Swift' events:")
    swift_events = fetch_events(keyword="Taylor Swift")
    print(f"Found {len(swift_events['events'])} Taylor Swift events")
    if swift_events['events']:
        print("\nFirst Taylor Swift event details:")
        pprint(swift_events['events'][0])
    
    # Test 3: Search by city
    print("\n3. Searching for events in 'New York':")
    ny_events = fetch_events(city="New York")
    print(f"Found {len(ny_events['events'])} events in New York")
    if ny_events['events']:
        print("\nFirst New York event details:")
        pprint(ny_events['events'][0])

if __name__ == "__main__":
    test_api()
