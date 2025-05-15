import os
import json
import websocket
import threading
import base64
import pyaudio

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000  # OpenAI's sample rate

websocket_url = (
    "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
)
headers = ["Authorization: Bearer " + OPENAI_API_KEY, "OpenAI-Beta: realtime=v1"]

# Global Variables
current_response_id = None
ai_is_responding = False
response_text = " "
is_playing_audio = False
audio_stream = None
should_stop_audio = False

# Initialize PyAudio
p = pyaudio.PyAudio()
audio_lock = threading.Lock()


def play_audio_chunk(audio_data):
    """Play a single audio chunk directly."""
    global audio_stream, is_playing_audio, should_stop_audio

    if should_stop_audio:
        return

    with audio_lock:
        try:
            # Initialize stream if it doesn't exist
            if audio_stream is None:
                audio_stream = p.open(
                    format=FORMAT, channels=CHANNELS, rate=RATE, output=True
                )
                is_playing_audio = True

            # Play the chunk
            audio_stream.write(audio_data)
        except Exception as e:
            print(f"Error playing audio chunk: {e}")
            stop_audio()


def stop_audio():
    """Stop audio playback."""
    global audio_stream, is_playing_audio, should_stop_audio

    with audio_lock:
        try:
            print("Stopping audio playback...")
            should_stop_audio = True

            if audio_stream is not None:
                if audio_stream.is_active():
                    audio_stream.stop_stream()
                audio_stream.close()
                audio_stream = None
                is_playing_audio = False
        except Exception as e:
            print(f"Error stopping audio: {e}")
        finally:
            # Ensure the stream is reset even if an error occurs
            audio_stream = None
            is_playing_audio = False


def handle_function_call(ws, function_name, arguments_str, call_id):
    """Process a function call from the LLM and return the result."""
    try:
        # Parse arguments
        arguments = json.loads(arguments_str)

        result = None
        if function_name == "make_reservation":
            # Extract parameters from arguments
            party_name = arguments.get("party_name")
            date = arguments.get("date")
            time = arguments.get("time")
            party_size = arguments.get("party_size")
            extra_notes = arguments.get("extra_notes")

            # Call the function
            result = make_reservation(party_name, date, time, party_size, extra_notes)
        elif function_name == "get_popular_dishes":
            result = get_popular_dishes()
        elif function_name == "get_dish_details":
            dish_id = arguments.get("dish_id")
            result = get_dish_details(dish_id)
        elif function_name == "get_upcoming_reservation_availability":
            result = get_upcoming_reservation_availability()
        else:
            result = {"success": False, "message": f"Unknown function: {function_name}"}

        # Convert result to string if it's not already
        if not isinstance(result, str):
            result = json.dumps(result)

        # Send the function result back to the model
        print(type(result))
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": result,
            },
        }
        ws.send(json.dumps(event))

    except Exception as e:
        print(f"Error handling function call: {e}")


def get_user_input(ws):
    global current_response_id, ai_is_responding, response_text, ai_is_responding, should_stop_audio

    while True:
        user_input = input(">>>>>>>>>>>>> \n")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            stop_audio()
            ws.close()
            break

        # Check if AI is currently responding
        if ai_is_responding and current_response_id:
            print("[Interrupting previous response...]")

            # Set the stop flag before stopping audio
            should_stop_audio = True

            # Stop audio playback
            stop_audio()

            # Cancel the current response
            cancel_event = {
                "type": "response.cancel",
                "response_id": current_response_id,
            }
            ws.send(json.dumps(cancel_event))

            # Wait a moment for cancellation to process
            # This isn't strictly necessary but can help prevent race conditions
            threading.Event().wait(0.1)

        # Send the user message
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": user_input}],
            },
        }
        ws.send(json.dumps(event))


def on_open(ws):
    print("Connected to server.")

    # Send the system message to set the agent's behavior and persona
    # Send the system message to set the agent's behavior and persona with function calling
    system_message = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": "You are an agent who makes restaurant reservations. To make a reservation, you need to collect the following required information: name of the party, date, time, and the size of the party. All these fields are required. You should talk like a restaurant front desk assistant gathering this information in a friendly, professional manner. Before finalizing any reservation, you must restate all the reservation details to the user and ask for confirmation. Only when the user confirms all details should you make the reservation by calling the make_reservation function. You have a bunch of tools at your disposal. When the user asks you about popular dishes or what's good in the restaurant, only stick to details returned from function call. Don't make up names of dishes, prices, or anything else that's not returned to you from the function.",
                }
            ],
        },
    }
    ws.send(json.dumps(system_message))

    # Start input thread
    input_thread = threading.Thread(target=get_user_input, args=(ws,))
    input_thread.daemon = True
    input_thread.start()


def on_message(ws, message):
    global current_response_id, ai_is_responding, response_text, should_stop_audio

    data = json.loads(message)
    event_type = data.get("type")

    if event_type not in [
        "response.text.delta",
        "response.audio.delta",
        "response.audio_transcript.delta",
    ]:
        print(event_type)

    if event_type == "conversation.item.created":
        ws.send(
            json.dumps(
                {
                    "type": "response.create",
                    "response": {
                        "modalities": ["text", "audio"],
                        "tools": function_definitions,
                        "tool_choice": "auto",
                    },
                }
            )
        )
    elif event_type == "response.text.delta":
        text_chunk = data["delta"]
        response_text += text_chunk

    elif event_type == "response.function_call_arguments.done":
        # Handle function call from the LLM
        function_name = data.get("name")
        arguments = data.get("arguments", "{}")
        call_id = data.get("call_id")

        # IMPORTANT: First, add a function_call item to the conversation history
        function_call_event = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call",
                "call_id": call_id,
                "name": function_name,
                "arguments": arguments,
            },
        }
        ws.send(json.dumps(function_call_event))

        # Wait a moment for this to be processed
        threading.Event().wait(0.2)

        # Now execute the function and send the output
        handle_function_call(ws, function_name, arguments, call_id)

    elif event_type == "response.audio.delta":
        # Process and play audio chunk immediately

        audio_data = base64.b64decode(data["delta"])
        play_audio_chunk(audio_data)

    elif event_type == "response.audio.done":
        ai_is_responding = False
        current_response_id = None
        response_text = ""

    elif event_type == "response.created":
        # A new response has been created, store its ID
        current_response_id = data.get("response", {}).get("id")
        ai_is_responding = True
        response_text = ""
        should_stop_audio = False

    elif event_type == "error":
        print(data)


def main():
    # Create and configure websocket
    ws = websocket.WebSocketApp(
        websocket_url,
        header=headers,
        on_open=on_open,
        on_message=on_message,
    )

    # Start the websocket client
    ws.run_forever()


### ------------------------------------------------ HELPER FUNCTIONS ------------------------------------------------------------- ###
# Function definitions for the LLM to call
import datetime

# Storage for reservations
reservations = []


# Function definitions for the LLM to call
function_definitions = [
    {
        "type": "function",
        "name": "make_reservation",
        "description": "Make a restaurant reservation with the provided details",
        "parameters": {
            "type": "object",
            "properties": {
                "party_name": {
                    "type": "string",
                    "description": "Name for the reservation",
                },
                "date": {
                    "type": "string",
                    "description": "Date of the reservation (YYYY-MM-DD)",
                },
                "time": {
                    "type": "string",
                    "description": "Time of the reservation (HH:MM)",
                },
                "party_size": {
                    "type": "integer",
                    "description": "Number of people in the party",
                },
                "extra_notes": {
                    "type": "string",
                    "description": "Any extra notes for the reservation",
                },
            },
            "required": ["party_name", "date", "time", "party_size"],
        },
    },
    {
        "type": "function",
        "name": "get_popular_dishes",
        "description": "Get a list of popular dishes with their IDs",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "get_dish_details",
        "description": "Get details of a dish by its ID, including ingredients, calories, prices, and user reviews",
        "parameters": {
            "type": "object",
            "properties": {
                "dish_id": {"type": "integer", "description": "ID of the dish"}
            },
            "required": ["dish_id"],
        },
    },
    {
        "type": "function",
        "name": "get_upcoming_reservation_availability",
        "description": "Check upcoming availability for reservations. Always call this function to confirm availability after the user has provided their preferred reservation date. True means available, False means not available for a given date.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]


def get_popular_dishes():
    """Function to return popular dishes with their corresponding IDs."""
    # This function could be expanded to fetch data from a database or an API
    # For now, we'll return a static list of popular dishes
    return [
        {"id": 1, "name": "Spaghetti Carbonara"},
        {"id": 2, "name": "Margherita Pizza"},
        {"id": 3, "name": "Caesar Salad"},
        {"id": 4, "name": "Grilled Salmon"},
        {"id": 5, "name": "Tiramisu"},
        {"id": 6, "name": "Ribeye Steak"},
        {"id": 7, "name": "Panna Cotta"},
        {"id": 8, "name": "Mushroom Risotto"},
        {"id": 9, "name": "Bruschetta"},
        {"id": 10, "name": "Caprese Salad"},
    ]


def get_dish_details(dish_id):
    # For every dish, return ingredients, calories, prices and generate 5 user reviews
    # For now, store everything in a static list corresponding to the dishes available in get_popular_dishes
    # This function could be expanded to fetch data from a database or an API
    # For now, we'll return a static list of popular dishes
    dishes = {
        1: {
            "name": "Spaghetti Carbonara",
            "ingredients": [
                "spaghetti",
                "eggs",
                "parmesan cheese",
                "pancetta",
                "black pepper",
            ],
            "calories": 600,
            "price": 12.99,
            "reviews": [
                {"user": "Alice", "review": "Delicious and creamy!"},
                {"user": "Bob", "review": "A bit too salty for my taste."},
                {"user": "Charlie", "review": "Perfectly cooked pasta!"},
                {"user": "David", "review": "My favorite dish here!"},
                {"user": "Eve", "review": "Authentic Italian flavor."},
            ],
        },
        # Add details for other dishes similarly
        2: {
            "name": "Margherita Pizza",
            "ingredients": [
                "pizza dough",
                "tomato sauce",
                "mozzarella cheese",
                "basil",
            ],
            "calories": 800,
            "price": 10.99,
            "reviews": [
                {"user": "Frank", "review": "Classic and simple, love it!"},
                {"user": "Grace", "review": "The crust was a bit soggy."},
                {"user": "Heidi", "review": "Fresh ingredients make a difference."},
                {"user": "Ivan", "review": "Best pizza in town!"},
                {"user": "Judy", "review": "A bit pricey for what you get."},
            ],
        },
        3: {
            "name": "Caesar Salad",
            "ingredients": [
                "romaine lettuce",
                "croutons",
                "parmesan cheese",
                "Caesar dressing",
            ],
            "calories": 350,
            "price": 8.99,
            "reviews": [
                {"user": "Karl", "review": "Crisp and refreshing!"},
                {"user": "Laura", "review": "Too much dressing for my liking."},
                {"user": "Mallory", "review": "Great as a side dish."},
                {"user": "Nina", "review": "Perfectly seasoned."},
                {"user": "Oscar", "review": "I could eat this every day!"},
            ],
        },
        4: {
            "name": "Grilled Salmon",
            "ingredients": ["salmon fillet", "olive oil", "lemon", "herbs"],
            "calories": 450,
            "price": 18.99,
            "reviews": [
                {"user": "Peggy", "review": "Cooked to perfection!"},
                {"user": "Quentin", "review": "A bit dry for my taste."},
                {"user": "Rupert", "review": "Flavors were amazing."},
                {"user": "Sybil", "review": "Healthy and delicious."},
                {"user": "Trent", "review": "I love the lemon zest."},
            ],
        },
        5: {
            "name": "Tiramisu",
            "ingredients": [
                "ladyfingers",
                "mascarpone cheese",
                "coffee",
                "cocoa powder",
            ],
            "calories": 400,
            "price": 6.99,
            "reviews": [
                {"user": "Uma", "review": "The best dessert ever!"},
                {"user": "Victor", "review": "Too sweet for my liking."},
                {"user": "Walter", "review": "Perfect end to a meal."},
                {"user": "Xena", "review": "I could eat this all day."},
                {"user": "Yara", "review": "Authentic Italian dessert."},
            ],
        },
        6: {
            "name": "Ribeye Steak",
            "ingredients": ["ribeye steak", "salt", "pepper", "butter"],
            "calories": 700,
            "price": 24.99,
            "reviews": [
                {"user": "Zara", "review": "Juicy and tender!"},
                {"user": "Aaron", "review": "Cooked exactly as I ordered."},
                {"user": "Bella", "review": "A bit too fatty for my taste."},
                {"user": "Cody", "review": "Best steak I've ever had!"},
                {"user": "Diana", "review": "Perfectly seasoned."},
            ],
        },
        7: {
            "name": "Panna Cotta",
            "ingredients": ["cream", "sugar", "gelatin", "vanilla"],
            "calories": 300,
            "price": 5.99,
            "reviews": [
                {"user": "Ethan", "review": "Silky smooth and delicious!"},
                {"user": "Fiona", "review": "A bit too sweet for my liking."},
                {"user": "George", "review": "Perfectly creamy."},
                {"user": "Hannah", "review": "Great texture."},
                {"user": "Ian", "review": "I love the vanilla flavor."},
            ],
        },
        8: {
            "name": "Mushroom Risotto",
            "ingredients": ["arborio rice", "mushrooms", "parmesan cheese", "broth"],
            "calories": 500,
            "price": 14.99,
            "reviews": [
                {"user": "Jack", "review": "Creamy and flavorful!"},
                {"user": "Kathy", "review": "A bit too rich for my taste."},
                {"user": "Leo", "review": "Perfectly cooked rice."},
                {"user": "Mia", "review": "Great comfort food."},
                {"user": "Nate", "review": "I love the mushroom flavor."},
            ],
        },
        9: {
            "name": "Bruschetta",
            "ingredients": ["bread", "tomatoes", "basil", "olive oil"],
            "calories": 250,
            "price": 7.99,
            "reviews": [
                {"user": "Olivia", "review": "Fresh and tasty!"},
                {"user": "Paul", "review": "A bit too garlicky for my taste."},
                {"user": "Quinn", "review": "Perfect appetizer."},
                {"user": "Rachel", "review": "I love the fresh tomatoes."},
                {"user": "Sam", "review": "Great with a glass of wine."},
            ],
        },
        10: {
            "name": "Caprese Salad",
            "ingredients": ["mozzarella cheese", "tomatoes", "basil", "olive oil"],
            "calories": 300,
            "price": 9.99,
            "reviews": [
                {"user": "Tina", "review": "Fresh and delicious!"},
                {"user": "Ursula", "review": "A bit too oily for my taste."},
                {"user": "Victor", "review": "Perfectly balanced flavors."},
                {"user": "Wendy", "review": "Great as a side dish."},
                {"user": "Xander", "review": "I love the fresh basil."},
            ],
        },
    }
    # Return the details of the requested dish
    dish_details = dishes.get(dish_id)
    if dish_details:
        return {
            "name": dish_details["name"],
            "ingredients": dish_details["ingredients"],
            "calories": dish_details["calories"],
            "price": dish_details["price"],
            "reviews": dish_details["reviews"],
        }
    else:
        return {"error": "Dish not found"}


def get_upcoming_reservation_availability():
    return {
        "2025-05-15": True,
        "2025-05-16": True,
        "2025-05-17": False,
        "2025-05-18": True,
        "2025-05-19": True,
        "2025-05-20": True,
        "2025-05-21": True,
        "2025-05-22": True,
        "2025-05-23": True,
        "2025-05-24": True,
        "2025-05-25": True,
        "2025-05-26": False,
        "2025-05-27": True,
        "2025-05-28": False,
        "2025-05-29": True,
        "2025-05-30": True,
        "2025-05-31": False,
    }


def make_reservation(party_name, date, time, party_size, extra_notes=None):
    """Function to make a reservation and store it."""
    # Validate the parameters

    # Perform basic validation
    if not all([party_name, date, time, party_size]):
        return {
            "success": False,
            "message": "All fields are required for a reservation.",
        }

    # You could add more validation here (date format, time format, etc.)

    # Create reservation record
    reservation = {
        "id": len(reservations) + 1,
        "name": party_name,
        "date": date,
        "time": time,
        "party_size": party_size,
        "created_at": datetime.datetime.now().isoformat(),
        "extra_notes": extra_notes,
    }

    # Store the reservation
    reservations.append(reservation)
    print(f"Reservation made: {reservation}")
    return {
        "success": True,
        "message": f"Reservation confirmed for {party_name} on {date} at {time} for {party_size} people.",
        "reservation_id": reservation["id"],
    }


### ------------------------------------------------ END HELPER FUNCTIONS ------------------------------------------------------------- ###

if __name__ == "__main__":
    try:
        main()
    finally:
        # Clean up PyAudio
        p.terminate()
