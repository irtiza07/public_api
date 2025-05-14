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

    # Start input thread
    input_thread = threading.Thread(target=get_user_input, args=(ws,))
    input_thread.daemon = True
    input_thread.start()


def on_message(ws, message):
    global current_response_id, ai_is_responding, response_text, should_stop_audio

    data = json.loads(message)
    event_type = data.get("type")
    print(event_type)

    if event_type == "response.text.delta":
        text_chunk = data["delta"]
        response_text += text_chunk

    elif event_type == "response.audio.delta":
        # Process and play audio chunk immediately

        audio_data = base64.b64decode(data["delta"])
        play_audio_chunk(audio_data)

    elif event_type == "response.audio.done":
        # Audio generation is complete
        print("\n[Audio complete]")

        # Clean up audio stream after a short delay
        # to ensure all audio has been played
        if not should_stop_audio:
            stop_audio()
            should_stop_audio = False

    elif event_type == "conversation.item.created":
        ws.send(
            json.dumps(
                {
                    "type": "response.create",
                    "response": {"modalities": ["text", "audio"]},
                }
            )
        )
    elif event_type == "response.created":
        # A new response has been created, store its ID
        current_response_id = data.get("response", {}).get("id")
        ai_is_responding = True
        response_text = ""
        should_stop_audio = False

    elif event_type == "response.done":
        # Response is complete
        # print(response_text)
        # print("STATUS: ", data["response"]["status"])
        ai_is_responding = False
        current_response_id = None
        response_text = ""


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


if __name__ == "__main__":
    try:
        main()
    finally:
        # Clean up PyAudio
        p.terminate()
