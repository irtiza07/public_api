"""
OpenAI Responses API Function Calling - Intermediate: Consecutive Function Calling

This demonstrates how the model can make multiple consecutive function calls,
using the output of one function as input to another function.
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
    Handle a user query with potential MULTIPLE consecutive function calls.
    
    The model may chain function calls together, using the output of one
    function as input to another. For example:
    1. get_event_location("wedding") → "Miami, USA"
    2. get_weather(location="Miami, USA") → weather data
    3. Final answer combining both results
    
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
            instructions="You are a helpful assistant with access to weather, todo, traffic, and event location tools.",
            tools=FUNCTION_SCHEMAS
        )

        # Loop to handle multiple consecutive function calls
        max_iterations = 5  # Safety limit to prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            # Collect ALL function calls from this response
            function_calls = [
                item for item in response.output 
                if hasattr(item, 'type') and item.type == "function_call"
            ]
            
            # Debug: Show how many function calls we found
            print(f"📊 Found {len(function_calls)} function call(s) in this response")
            for idx, fc in enumerate(function_calls, 1):
                print(f"   {idx}. {fc.name}({fc.arguments})")
            
            # If no function calls, we have the final answer
            if not function_calls:
                print(f"\n✨ Final answer received after {iteration} iteration(s)!")
                return {"status": "success", "response": response, "iterations": iteration}
            
            # Process ALL function calls from this iteration
            for fc_item in function_calls:
                print(f"\n🔧 Processing function: {fc_item.name}")
                print(f"📋 Arguments: {fc_item.arguments}")
                
                if fc_item.name in AVAILABLE_FUNCTIONS:
                    func = AVAILABLE_FUNCTIONS[fc_item.name]
                    func_args = json.loads(fc_item.arguments)

                    # Call the function with unpacked arguments
                    func_result = func(**func_args)
                    print(f"✅ Function result: {func_result}")

                    # Append the function call output to the conversation history
                    conversation_history.append({
                        "type": "function_call_output",
                        "call_id": fc_item.call_id,
                        "output": json.dumps(func_result),
                    })
            
            # After processing ALL function calls, send results back
            print(f"\n📤 Sending {len(function_calls)} function result(s) back to model...")
            response = client.responses.create(
                model="gpt-4o",
                previous_response_id=response.id,
                input=conversation_history,
                tools=FUNCTION_SCHEMAS,
            )
        
        # If we hit max iterations
        print(f"\n⚠️ Warning: Reached maximum iterations ({max_iterations})")
        return {"status": "error", "error": "Maximum iterations reached", "response": response}
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"status": "error", "error": str(e)}


def interactive_mode():
    """Interactive mode for testing queries that may require consecutive function calls."""
    print("🎮 Interactive Mode - Type 'quit' to exit")
    print("\nTry queries that require multiple function calls:")
    print("  • 'What's the weather like for my conference?'")
    print("  • 'Should I bring an umbrella to my wedding?'")
    print("  • 'Will it rain during my business trip?'\n")
    
    while True:
        # Initialize an empty conversation history for each query
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
