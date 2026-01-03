"""
OpenAI Responses API - Streaming with Function Calling

This demonstrates how to handle streaming responses when the model makes function calls.
Shows all event types and highlights key events like function calls with their arguments.
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


def handle_streaming_query(user_query: str, previous_response_id: str = None) -> Dict[str, Any]:
    """
    Handle a user query with streaming and function calling.
    
    Prints:
    1. All event types from the stream
    2. Key events (function calls, arguments, results)
    
    Args:
        user_query: The user's question or request
        previous_response_id: ID of the previous response to continue the conversation
        
    Returns:
        Dictionary with final response and collected data
    """
    
    print(f"🔍 User Query: {user_query}")
    
    # Track accumulated data
    function_calls = {}  # {item_id: {name, arguments, call_id}}
    response_id = None
    complete_response = None
    
    try:
        print("\n📡 Starting streaming request...")
        
        # Create streaming request
        stream = client.responses.create(
            model="gpt-4o",
            input=user_query,
            previous_response_id=previous_response_id,
            instructions="You are a helpful assistant with access to weather, todo, traffic, and event location tools.",
            tools=FUNCTION_SCHEMAS,
            stream=True
        )
        
        # Process stream events
        print("\n--- Stream Events ---")
        for event in stream:
            event_type = event.type
            
            # 1. Print EVERY event type (raw data)
            print(f"📊 EVENT: {event_type}")
            
            # 2. Highlight KEY events with details
            if event_type == "response.output_item.added":
                item = event.item
                print(f"   ✨ Item Type: {item.type}, ID: {item.id}")
                
                if item.type == "function_call":
                    print(f"      🔧 Function: {item.name}")
                    print(f"      📞 Call ID: {item.call_id}")
                    
                    # Initialize tracking
                    function_calls[item.id] = {
                        "name": item.name,
                        "call_id": item.call_id,
                        "arguments": ""
                    }
            
            elif event_type == "response.function_call_arguments.delta":
                item_id = event.item_id
                delta = event.delta
                print(f"   📝 Args chunk: '{delta}'")
                
                if item_id in function_calls:
                    function_calls[item_id]["arguments"] += delta
            
            elif event_type == "response.function_call_arguments.done":
                item_id = event.item_id
                arguments = event.arguments
                print(f"   ✅ Complete args: {arguments}")
                
                if item_id in function_calls:
                    function_calls[item_id]["arguments"] = arguments
            
            elif event_type == "response.output_item.done":
                item = event.item
                print(f"   🏁 Item finished: {item.type} (ID: {item.id})")
            
            elif event_type == "response.done" or event_type == "response.completed":
                complete_response = event.response
                response_id = event.response.id
                print(f"   🎉 Response ID: {response_id}")
        
        # After stream completes, execute function calls if any
        if function_calls:
            print(f"\n--- Executing {len(function_calls)} Function Call(s) ---")
            
            function_outputs = []
            for item_id, fc_data in function_calls.items():
                func_name = fc_data["name"]
                func_args_str = fc_data["arguments"]
                call_id = fc_data["call_id"]
                
                print(f"\n🔧 Function: {func_name}")
                print(f"📋 Arguments: {func_args_str}")
                
                if func_name in AVAILABLE_FUNCTIONS:
                    func = AVAILABLE_FUNCTIONS[func_name]
                    func_args = json.loads(func_args_str)
                    
                    # Execute the function
                    func_result = func(**func_args)
                    print(f"✅ Result: {func_result}")
                    
                    # Collect the function call output
                    function_outputs.append({
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(func_result),
                    })
            
            # Send function results back
            print(f"\n📤 Sending {len(function_calls)} result(s) back to model...")
            
            followup = client.responses.create(
                model="gpt-4o",
                previous_response_id=response_id,
                input=function_outputs,
                tools=FUNCTION_SCHEMAS,
            )
            
            return {
                "status": "success",
                "response": followup,
                "function_calls": function_calls
            }
        else:
            # No function calls, return the response from the stream
            return {
                "status": "success",
                "response": complete_response
            }
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return {"status": "error", "error": str(e)}


def interactive_mode():
    """Interactive mode for testing streaming with function calls."""
    print("🎮 Streaming Mode - Type 'quit' to exit")
    print("\nTry queries that invoke functions:")
    print("  • 'What's the weather for my conference?'")
    print("  • 'What's the weather in Miami and Chicago?'")
    print("  • 'Show me high priority tasks'\n")
    previous_response_id = None
    
    while True:
        user_input = input("\n💭 Your query: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        elif not user_input:
            continue
        
        final_result = handle_streaming_query(user_input, previous_response_id)
        previous_response_id = final_result['response'].id
        
        if final_result.get('status') == 'success':
            # Print final answer similar to logic_intermediate.py
            print("\n" + "="*70)
            print("💬 FINAL ANSWER:")
            print("="*70)
            print(final_result['response'].output[0].content[0].text)
        else:
            print(f"\n❌ Error: {final_result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    print("🚀 OpenAI Responses API - Streaming with Function Calling\n")
    interactive_mode()
