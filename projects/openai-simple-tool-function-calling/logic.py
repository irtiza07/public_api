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


def handle_user_query(user_query: str, conversation_history: list) -> Dict[str, Any]:
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
        # Append the user query to the conversation history
        conversation_history.append({"role": "user", "content": user_query})

        # Call Responses API with the full conversation history
        response = client.responses.create(
            model="gpt-4o",
            input=conversation_history,
            instructions="You are a helpful assistant with access to weather, todo, and traffic tools.",
            tools=FUNCTION_SCHEMAS
        )

        # Append the assistant's response to the conversation history
        if hasattr(response, 'output'):
            for item in response.output:
                if hasattr(item, 'role') and item.role == "assistant":
                    conversation_history.append({"role": "assistant", "content": item.content})

        # Look for function calls in the response
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

                    # Append the function call output to the conversation history
                    conversation_history.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(func_result),
                    })

                    # Send the function result back to the model
                    followup = client.responses.create(
                        model="gpt-4o",
                        previous_response_id=response.id,
                        input=conversation_history,
                        tools=FUNCTION_SCHEMAS,
                    )

                    # Append the follow-up response to the conversation history
                    if hasattr(followup, 'output'):
                        for followup_item in followup.output:
                            if hasattr(followup_item, 'role') and followup_item.role == "assistant":
                                conversation_history.append({"role": "assistant", "content": followup_item.content})

                    return {"status": "success", "response": followup}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"status": "error", "error": str(e)}


def interactive_mode():
    """Simple interactive mode for testing queries."""
    print("🎮 Interactive Mode - Type 'quit' to exit")
    
    while True:
        # Initialize an empty conversation history
        conversation_history = []
        user_input = input("\n💭 Your query: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        elif not user_input:
            continue

        final_result = handle_user_query(user_input, conversation_history)
        print(final_result['response'].output[0].content[0].text)


if __name__ == "__main__":
    interactive_mode()
