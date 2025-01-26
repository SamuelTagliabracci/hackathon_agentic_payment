import os
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.agents import Tool, AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools.render import render_text_description
from langchain.prompts import PromptTemplate
from ticket_data import concert_tickets

# Load environment variables
load_dotenv()

# Configure Google Gemini Pro
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def search_tickets(query: str) -> str:
    """Search available tickets based on the query"""
    # Search through sample concert data
    matching_events = []
    query = query.lower()
    
    for event in concert_tickets["events"]:
        # Search in event name, artist, venue, and description
        event_text = f"{event['name']} {event['artist']} {event['venue']} {event.get('description', '')}".lower()
        if query in event_text:
            matching_events.append(event)
    
    if not matching_events:
        return "No matching events found."
    return str({"events": matching_events})

def get_ticket_details(event_id: str) -> str:
    """Get detailed information about specific tickets"""
    # Search through sample concert data
    for event in concert_tickets["events"]:
        if event["id"] == event_id:
            return str(event)
    return "Event not found"

def process_purchase(ticket_info: Dict[str, Any]) -> str:
    """Process the ticket purchase by calling the transaction module"""
    try:
        # First call main.py to indicate purchase initiation
        call_main()
        
        # Import the transaction module dynamically
        import sys
        sys.path.append('../transaction')
        from process_transaction import process_payment
        
        # Call the process_payment function
        result = process_payment(ticket_info)
        return f"Purchase processed successfully: {result}"
    except Exception as e:
        return f"Error processing purchase: {str(e)}"

def call_main() -> str:
    """Execute the main.py file in the root directory"""
    try:
        import subprocess
        import os
        
        # Get the root directory path
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_path = os.path.join(root_dir, 'main.py')
        
        # Run the main.py script
        result = subprocess.run(['python', main_path], capture_output=True, text=True)
        return result.stdout if result.stdout else "Main script executed successfully"
    except Exception as e:
        return f"Error executing main script: {str(e)}"

# Define tools for the agent
tools = [
    Tool(
        name="SearchTickets",
        func=search_tickets,
        description="Search for available concert tickets. Input should be a string with search criteria."
    ),
    Tool(
        name="GetTicketDetails",
        func=get_ticket_details,
        description="Get detailed information about specific tickets. Input should be the event ID."
    ),
    Tool(
        name="ProcessPurchase",
        func=process_purchase,
        description="Process the ticket purchase. Input should be a dictionary with ticket details."
    ),
    Tool(
        name="CallMain",
        func=call_main,
        description="Execute the main.py script from the root directory."
    )
]

# Create the Gemini Pro agent
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)

# Define the agent prompt
template = """You are a helpful concert ticket booking assistant. You can help users find and purchase concert tickets.
You have access to the following tools:

{tools}

Use these tools to help the user find and purchase tickets.
Always be polite and professional.
Make sure to get all necessary information before processing a purchase.

When you want to take an action:
1. First think about what tool would be most appropriate
2. Then use the tool in this format:
Action: <tool_name>
Action Input: <input>

{chat_history}
Question: {input}
{agent_scratchpad}

Let's approach this step by step:
1) First, I'll think about what the user is asking for
2) Then, I'll choose the appropriate tool to help
3) Finally, I'll provide a helpful response

"""

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
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print("Welcome to the Concert Ticket Booking System!")
    print("You can ask about available tickets, get details, or make a purchase.")
    print("Type 'quit' to exit.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            break
            
        response = chat_with_agent(user_input)
        print(f"\nAssistant: {response}")
