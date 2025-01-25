import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain.agents import Tool, AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain_openai import ChatOpenAI
from langchain.tools.render import render_text_description
from langchain.prompts import PromptTemplate
from ticket_data import concert_tickets
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def format_event_details(event: Dict) -> str:
    """Format event details in a readable way"""
    try:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').strftime('%A, %B %d, %Y')
        details = f"""
 {event['artist']}
 {event['venue']}
 {event_date}
 {event['time']}

Available Tickets:"""
        
        for ticket in event['available_tickets']:
            details += f"\n• {ticket['section']} (Row {ticket['row']}): ${ticket['price']:.2f} ({ticket['quantity']} available)"
        
        return details
    except Exception as e:
        return str(event)

def search_tickets(query: str) -> str:
    """Search available tickets based on the query"""
    from ticket_data import fetch_events
    events = fetch_events(keyword=query)
    
    if not events['events']:
        return "No events found matching your search criteria. Would you like to try a different search?"
    
    response = "Here are the events I found:\n"
    for i, event in enumerate(events['events'], 1):
        response += f"\nEvent {i} (ID: {event['id']})\n"
        response += format_event_details(event)
        response += "\n" + "-"*50
    
    return response

def get_ticket_details(event_id: str) -> str:
    """Get detailed information about specific tickets"""
    from ticket_data import fetch_events, concert_tickets
    
    # First try to find in fetched events
    events = fetch_events()
    for event in events["events"]:
        if event["id"] == event_id:
            return format_event_details(event)
    
    # Fallback to sample data
    for event in concert_tickets["events"]:
        if event["id"] == event_id:
            return format_event_details(event)
    
    return "Event not found. Please check the event ID and try again."

def process_purchase(ticket_info_str: str) -> str:
    """Process the ticket purchase by calling the transaction module"""
    try:
        # Parse the ticket info string into a dictionary
        ticket_info = json.loads(ticket_info_str)
        required_fields = ['event_id', 'section', 'quantity', 'total_price']
        
        # Validate required fields
        missing_fields = [field for field in required_fields if field not in ticket_info]
        if missing_fields:
            return f"Missing required information: {', '.join(missing_fields)}"
        
        # Import the transaction module dynamically
        import sys
        sys.path.append('../transaction')
        from process_transaction import process_payment
        
        # Call the process_payment function
        result = process_payment(ticket_info)
        return f" Purchase successful!\n\nOrder Details:\n- Event ID: {ticket_info['event_id']}\n- Section: {ticket_info['section']}\n- Quantity: {ticket_info['quantity']}\n- Total: ${ticket_info['total_price']:.2f}\n\nThank you for your purchase! Your tickets will be emailed to you shortly."
    except json.JSONDecodeError:
        return "Invalid ticket information format. Please provide the information in the correct format."
    except Exception as e:
        return f"Error processing purchase: {str(e)}"

# Define tools for the agent
tools = [
    Tool(
        name="SearchTickets",
        func=search_tickets,
        description="Search for available concert tickets. Input should be a search query (e.g., artist name, city, or 'all' for all events)."
    ),
    Tool(
        name="GetTicketDetails",
        func=get_ticket_details,
        description="Get detailed information about a specific event. Input should be the event ID."
    ),
    Tool(
        name="ProcessPurchase",
        func=process_purchase,
        description="Process the ticket purchase. Input should be a JSON string with event_id, section, quantity, and total_price."
    )
]

# Create the GPT-4 agent
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    api_key=OPENAI_API_KEY
)

# Define the agent prompt
template = """You are a helpful and enthusiastic concert ticket booking assistant. You help users find and purchase concert tickets while maintaining a friendly and professional tone.

You have access to the following tools:

{tools}

Follow these guidelines:
1. When searching for tickets:
   - Ask for specific preferences (artist, city, date range)
   - Present options clearly with event IDs
   - Highlight important details (price, availability)

2. When processing purchases:
   - Confirm all details before processing
   - Ensure quantity is available
   - Format the purchase information as proper JSON
   - Double-check total price calculations

3. Always be helpful:
   - Suggest alternatives if events are not found
   - Provide relevant recommendations
   - Handle errors gracefully
   - Maintain context of the conversation

{chat_history}
Question: {input}
{agent_scratchpad}

Let's help this customer find their perfect concert tickets!"""

prompt = PromptTemplate.from_template(template)

# Create the agent
agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x.get("chat_history", ""),
        "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        "tools": lambda x: render_text_description(tools),
    }
    | prompt
    | llm
    | ReActSingleInputOutputParser()
)

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3
)

def chat_with_agent(user_input: str) -> str:
    """Function to interact with the agent"""
    try:
        response = agent_executor.invoke({"input": user_input})
        return response["output"]
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}\nHow else can I help you with your ticket search?"

if __name__ == "__main__":
    print("""
 Welcome to the Concert Ticket Booking System! 

I can help you:
• Search for concerts by artist, city, or date
• Get detailed event information
• Purchase tickets securely

Just let me know what you're looking for! Type 'quit' to exit.
""")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            print("\nThank you for using our ticket booking service! Have a great day! ")
            break
            
        response = chat_with_agent(user_input)
        print(f"\nAssistant: {response}")
