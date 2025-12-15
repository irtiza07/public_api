import os
import sys
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import json

from logic import generate_chapters_from_transcript

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Ask user for local file path
file_path = input("Enter the full path to your local audio file: ").strip()
if not os.path.isfile(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

# Extract file name (without extension) to use as ID
video_id = Path(file_path).stem

# Transcribe using OpenAI Whisper API
client = OpenAI(api_key=OPENAI_API_KEY)

print("Transcribing audio (with timestamps)...")
with open(file_path, "rb") as audio_file:
    transcript_verbose = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        language="en"
    )

# Prepare output directory
output_dir = Path("generated")
output_dir.mkdir(exist_ok=True)

# Save transcript with timestamps
json_path = output_dir / f"{video_id}_timestamps.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(transcript_verbose.model_dump(), f, ensure_ascii=False, indent=2)
print(f"Saved transcript with timestamps to {json_path}")


try:
    generate_chapters_from_transcript(json_path, output_dir, video_id, client)
except Exception as e:
    print(f"[Warning] Could not generate YouTube chapters: {e}")

print("Done!")
