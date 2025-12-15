import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- Generate YouTube Chapters ---
def generate_chapters_from_transcript(json_path, output_dir, video_id, openai_client):
    with open(json_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
    # Extract segments with timestamps and text
    segments = transcript_data.get("segments", [])
    # Build a summary string for GPT
    summary_lines = []
    for seg in segments:
        start = int(seg["start"])
        minutes = start // 60
        seconds = start % 60
        timestamp = f"{minutes}:{seconds:02d}"
        text = seg["text"].strip().replace("\n", " ")
        what_to_append_for_each_segment = f"{timestamp} {text}"
        print(what_to_append_for_each_segment)
        summary_lines.append(what_to_append_for_each_segment)
    summary_for_gpt = "\n".join(summary_lines)
    prompt = (
        "Given the following transcript segments with timestamps, generate YouTube chapters in the format: '0:00 Title' (timestamp and a short title). "
        "Only output the chapters list, nothing else.\n\n" + summary_for_gpt
    )
    print("Generating YouTube chapters using GPT...")
    # Use the global client
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes transcripts into YouTube chapters."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        temperature=0.3,
    )
    chapters_text = response.choices[0].message.content.strip()
    chapters_path = output_dir / f"{video_id}.chapters.txt"
    with open(chapters_path, "w", encoding="utf-8") as f:
        f.write(chapters_text)
    print(f"Saved YouTube chapters to {chapters_path}")