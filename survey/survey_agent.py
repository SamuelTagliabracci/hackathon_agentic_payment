import os
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from langchain.agents import Tool, AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain_openai import ChatOpenAI
from langchain.tools.render import render_text_description
from langchain.prompts import PromptTemplate
from survey_data import sample_concerts

# Load environment variables
load_dotenv()

def find_closest_concert(city: str, date_str: str) -> str:
    """Find the closest concert based on city and date"""
    try:
        # Parse the input date
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        target_city = city.lower()
        
        # Initialize variables for finding the best match
        best_match = None
        min_date_diff = float('inf')
        
        for concert in sample_concerts["concerts"]:
            concert_date = datetime.strptime(concert["date"], "%Y-%m-%d")
            concert_city = concert["city"].lower()
            
            # Calculate date difference in days
            date_diff = abs((concert_date - target_date).days)
            
            # If this is in the requested city and has a closer date, it's our new best match
            if concert_city == target_city and date_diff < min_date_diff:
                min_date_diff = date_diff
                best_match = concert
            
        if best_match:
            return f"Found concert: {best_match['name']} by {best_match['artist']} at {best_match['venue']} in {best_match['city']} on {best_match['date']}. Price: ${best_match['price']}"
        else:
            return f"No concerts found in {city} around {date_str}"
            
    except ValueError as e:
        return f"Error: Please provide date in YYYY-MM-DD format"

def list_available_concerts() -> str:
    """List all available concerts with numbers for selection"""
    concert_list = []
    for idx, concert in enumerate(sample_concerts["concerts"], 1):
        concert_list.append(
            f"{idx}. {concert['artist']} - {concert['name']}\n"
            f"   {concert['city']} at {concert['venue']}\n"
            f"   {concert['date']}\n"
            f"   ${concert['price']:.2f}\n"
        )
    return "\n".join(concert_list)

def call_main_script() -> str:
    """Execute the main.py script in the root directory"""
    try:
        import subprocess
        import os
        
        # Get the root directory path
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_path = os.path.join(root_dir, 'main.py')
        
        # Run the main.py script
        result = subprocess.run(['python', main_path], capture_output=True, text=True)
        return result.stdout if result.stdout else "Payment processing initiated..."
    except Exception as e:
        return f"Error executing payment process: {str(e)}"

def select_concert_by_number(number: str) -> str:
    """Select a concert by its number in the list"""
    try:
        idx = int(number)
        if 1 <= idx <= len(sample_concerts["concerts"]):
            concert = sample_concerts["concerts"][idx - 1]
            # First get the concert details
            selection_message = f"Selected concert: {concert['name']} by {concert['artist']} at {concert['venue']} in {concert['city']} on {concert['date']}. Price: ${concert['price']}"
            
            # Then call the main script
            payment_message = call_main_script()
            
            # Return combined message
            return f"{selection_message}\n{payment_message}"
        else:
            return "Invalid concert number. Please select a number from the list above."
    except ValueError:
        return "Please enter a valid number from the list above."

# Define tools for the agent
tools = [
    Tool(
        name="ListConcerts",
        func=list_available_concerts,
        description="List all available concerts with their details"
    ),
    Tool(
        name="SelectConcert",
        func=select_concert_by_number,
        description="Select a concert by its number (1-5) and process the payment"
    ),
    Tool(
        name="ProcessPayment",
        func=call_main_script,
        description="Process the payment for the selected concert"
    ),
    Tool(
        name="FindConcert",
        func=find_closest_concert,
        description="Find the closest concert to a given city and date. Input should be a city name and date in YYYY-MM-DD format, separated by comma."
    )
]

# Define the agent prompt
template = """You are a helpful concert booking assistant. Here's how you should interact with users:

1. When a user first connects or asks about available concerts, use the ListConcerts tool to show all available concerts.
2. After showing the list, tell the user they can select a concert by typing its number (1-5).
3. When a user enters a number, use the SelectConcert tool with that number to process their selection and payment.

You have access to the following tools:

{tools}

Use these tools to help the user find, select, and purchase concerts.
Always be polite and professional.

When you need to take an action, use this exact format:
Action: [ToolName]
Action Input: [Input]

Current conversation:
{chat_history}
Human: {input}
Assistant: {agent_scratchpad}"""

prompt = PromptTemplate(
    template=template,
    input_variables=["input", "chat_history", "agent_scratchpad", "tools"]
)

# Create the GPT-4 agent
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Create the agent
agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x.get("chat_history", []),
        "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        "tools": lambda x: render_text_description(tools)
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
    max_iterations=3,
    return_intermediate_steps=True,
)

def chat_with_agent(user_input: str):
    """Function to interact with the agent"""
    try:
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": []
        })
        return response["output"]
    except Exception as e:
        return "I apologize, but I encountered an error. Please enter a number between 1-5 to select a concert from the list."

if __name__ == "__main__":
    print("Welcome to the Concert Booking Assistant!")
    print("Here are the available concerts:\n")
    print(list_available_concerts())
    print("\nPlease enter a number (1-5) to select a concert, or type 'quit' to exit.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Thank you for using the Concert Booking Assistant. Goodbye!")
            break
            
        response = chat_with_agent(user_input)
        print(f"\nAssistant: {response}")
