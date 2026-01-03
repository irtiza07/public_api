"""
OpenAI Responses API Function Calling - Simple Skeleton

This is a minimal implementation for testing function calling with the Responses API.
"""

import os
import json
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from schemas import FUNCTION_SCHEMAS, AVAILABLE_FUNCTIONS

# Load environment and OpenAI client
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=api_key)


def handle_user_query(user_query: str, previous_response_id: str = None) -> Dict[str, Any]:
    """
    Handle a user query with potential function calling, maintaining conversation history.
    
    Args:
        user_query: The user's question or request.
        conversation_history: List maintaining the conversation history.
        
    Returns:
        Dictionary with results and function call details.
    """

    print(f"🔍 User Query: {user_query}")

    try:
        response = client.responses.create(
            model="gpt-4o",
            instructions="You are a helpful assistant with access to weather, todo, and traffic tools.",
            previous_response_id=previous_response_id,
            input=user_query,
            tools=FUNCTION_SCHEMAS
        )

        for item in response.output:
            if hasattr(item, 'type') and item.type == "function_call":
                print(f"🔧 Function called: {getattr(item, 'name', 'unknown')}")
                print(f"🤑 Function called: {getattr(item, 'arguments', 'unknown')}")
                if item.name in AVAILABLE_FUNCTIONS:
                    func = AVAILABLE_FUNCTIONS[item.name]
                    func_args = json.loads(item.arguments)

                    # Call the function with unpacked arguments
                    func_result = func(**func_args)
                    print(f"✅ Function result:\n{func_result}")

                    # Send the function result back to the model
                    followup = client.responses.create(
                        model="gpt-4o",
                        previous_response_id=response.id,
                        input=[{"type": "function_call_output", "output": func_result, "call_id": item.call_id}],
                        tools=FUNCTION_SCHEMAS,
                    )

                    return {"status": "success", "response": followup}
            else:
                return {"status": "success", "response": response}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"status": "error", "error": str(e)}


def interactive_mode():
    """Simple interactive mode for testing queries."""
    print("🎮 Interactive Mode - Type 'quit' to exit")
    previous_response_id = None
    
    while True:
        user_input = input("\n💭 Your query: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        elif not user_input:
            continue

        final_result = handle_user_query(user_input, previous_response_id)
        print(final_result['response'].output[0].content[0].text)
        previous_response_id = final_result['response'].id


if __name__ == "__main__":
    interactive_mode()
