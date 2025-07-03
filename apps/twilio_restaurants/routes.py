import os
import json
import base64
import asyncio
import websockets
import threading


from websockets.protocol import State as ConnectionState
from fastapi import APIRouter, FastAPI, WebSocket, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv

from logic.realtime_api_openai.reservations_agent.simple_websocket import (
    function_definitions,
    handle_function_call,
)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SYSTEM_MESSAGE = (
    "You are an agent who makes restaurant reservations."
    "To make a reservation, you need to collect the following required information: name of the party, date, time, and the size of the party."
    "All these fields are required"
    "You should talk like a restaurant front desk assistant gathering this information in a friendly, professional manner."
    "Before finalizing any reservation, you must restate all the reservation details to the user and ask for confirmation."
    "Only when the user confirms all details should you make the reservation by calling the make_reservation function."
    "You have a bunch of tools at your disposal. When the user asks you about popular dishes or what's good in the restaurant, only stick to details returned from function call."
    "Don't make up names of dishes, prices, or anything else that's not returned to you from the function."
)
VOICE = "alloy"

LOG_EVENT_TYPES = [
    "response.content.done",
    "rate_limits.updated",
    "response.done",
    "input_audio_buffer.committed",
    "input_audio_buffer.speech_stopped",
    "input_audio_buffer.speech_started",
    "session.created",
    "response.function_call_arguments.done",
    "error",
]

router = APIRouter()


@router.get("/", response_class=JSONResponse)
async def health():
    return {"message": "Twilio Media Stream Server is running..."}


@router.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    response = VoiceResponse()
    response.say("Please wait while we connect your call to the AI voice assistant.")
    response.pause(length=1)
    response.say("O.K. you can start talking now.")

    host = "7179-2605-a601-5591-e500-21b4-1198-6004-bd87.ngrok-free.app"
    connect = Connect()

    media_stream_url = f"wss://{host}/twilio_restaurants/media-stream"
    print(media_stream_url)
    connect.stream(url=media_stream_url)
    response.append(connect)

    return HTMLResponse(content=str(response), media_type="application/xml")


@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        },
    ) as openai_ws:
        await send_session_update(openai_ws)
        stream_sid = None

        async def receive_from_twilio():
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data["event"] == "start":
                        stream_sid = data["start"]["streamSid"]
                        print(f"Incoming stream has started {stream_sid}")
                    elif (
                        data["event"] == "media"
                        and openai_ws.state == ConnectionState.OPEN
                    ):
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data["media"]["payload"],
                        }
                        await openai_ws.send(json.dumps(audio_append))
            except WebSocketDisconnect:
                print("Client disconnected")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            nonlocal stream_sid
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response["type"] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}")
                    if response["type"] == "session.updated":
                        print("Session updated successfully:")
                    if response["type"] == "response.function_call_arguments.done":
                        # Handle function call from the LLM
                        function_name = response.get("name")
                        arguments = response.get("arguments", "{}")
                        call_id = response.get("call_id")

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
                        print("Sending function_call event to OpenAI API")
                        await openai_ws.send(json.dumps(function_call_event))

                        # Wait a moment for this to be processed
                        threading.Event().wait(0.2)

                        print("Calling function handle_function_call")
                        await handle_function_call(
                            ws=openai_ws,
                            function_name=function_name,
                            arguments_str=arguments,
                            call_id=call_id,
                        )

                        # Wait a moment for this to be processed
                        threading.Event().wait(0.2) 

                        await openai_ws.send(
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

                    if response["type"] == "response.audio.delta" and response.get(
                        "delta"
                    ):
                        try:
                            audio_payload = base64.b64encode(
                                base64.b64decode(response["delta"])
                            ).decode("utf-8")
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": audio_payload},
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())


async def send_session_update(openai_ws):
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
            "tools": function_definitions,
            "tool_choice": "auto",
        },
    }
    print(f"Sending session update...")
    await openai_ws.send(json.dumps(session_update))
