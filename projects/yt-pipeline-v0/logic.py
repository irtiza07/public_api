"""
YouTube Video Pipeline - Complete Workflow
Generates chapters, description, and thumbnail for YouTube videos
"""

import os
import sys
import json
import base64
import glob
from pathlib import Path
from typing import Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key: Optional[str] = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client: OpenAI = OpenAI(api_key=api_key)


def prompt_user(prompt: str) -> str:
    """
    Prompt the user for input and return the entered string.
    
    Args:
        prompt (str): The prompt message to display to the user.
    
    Returns:
        str: The user's input.
    """
    return input(prompt).strip()


def find_audio_file(project_dir: str) -> Optional[str]:
    """
    Search for audio.m4a file in the project directory.
    
    Args:
        project_dir (str): The directory to search in.
    
    Returns:
        Optional[str]: The path to the audio file if found, None otherwise.
    """
    audio_path = os.path.join(project_dir, "audio.m4a")
    if os.path.isfile(audio_path):
        return audio_path
    
    # Try to find any .m4a file
    m4a_files = glob.glob(os.path.join(project_dir, "*.m4a"))
    if m4a_files:
        return m4a_files[0]
    
    return None


def transcribe_audio(audio_path: str, output_dir: Path) -> Path:
    """
    Transcribe audio file using OpenAI Whisper API with timestamps.
    
    Args:
        audio_path (str): Path to the audio file.
        output_dir (Path): Directory to save the transcript.
    
    Returns:
        Path: Path to the saved JSON transcript file.
    """
    print("Transcribing audio with timestamps...")
    with open(audio_path, "rb") as audio_file:
        transcript_verbose = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            language="en"
        )
    
    json_path = output_dir / "audio_timestamps.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(transcript_verbose.model_dump(), f, ensure_ascii=False, indent=2)
    
    print(f"Transcript saved to {json_path}")
    return json_path


def generate_chapters(json_path: Path) -> str:
    """
    Generate YouTube chapters from transcript with timestamps.
    
    Args:
        json_path (Path): Path to the JSON transcript file.
    
    Returns:
        str: Generated chapters text.
    """
    print("Generating YouTube chapters...")
    
    with open(json_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
    
    segments = transcript_data.get("segments", [])
    summary_lines = []
    
    for seg in segments:
        start = int(seg["start"])
        minutes = start // 60
        seconds = start % 60
        timestamp = f"{minutes}:{seconds:02d}"
        text = seg["text"].strip().replace("\n", " ")
        summary_lines.append(f"{timestamp} {text}")
    
    summary_for_gpt = "\n".join(summary_lines)
    prompt = (
        "Given the following transcript segments with timestamps, generate YouTube chapters in the format: '0:00 Title' (timestamp and a short title). "
        "Only output the chapters list, nothing else.\n\n" + summary_for_gpt
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes transcripts into YouTube chapters."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        temperature=0.3,
    )
    
    chapters_text = response.choices[0].message.content.strip()
    print("Chapters generated successfully!")
    return chapters_text


def generate_video_summary(json_path: Path) -> str:
    """
    Generate a brief video summary from the transcript for use in the description.
    
    Args:
        json_path (Path): Path to the JSON transcript file.
    
    Returns:
        str: Generated video summary.
    """
    print("Generating video summary...")
    
    with open(json_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
    
    full_text = transcript_data.get("text", "")
    
    prompt = (
        "Summarize the following video transcript in 3 concise sentences for a YouTube video description. "
        "Make it engaging and informative:\n\n" + full_text
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that creates engaging YouTube video descriptions."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0.5,
    )
    
    summary = response.choices[0].message.content.strip()
    print("Summary generated successfully!")
    return summary


def generate_description(summary: str, chapters: str, github_url: str) -> str:
    """
    Generate YouTube description using the template.
    
    Args:
        summary (str): Video summary text.
        chapters (str): Generated chapters text.
        github_url (str): GitHub repository URL.
    
    Returns:
        str: Complete YouTube description.
    """
    description = f"""
        📍 Get notes and diagrams: https://irtizahafiz.com/newsletter?utm_source=yt
        ▶️ Get the code: {github_url}
        
        {summary}

        {chapters}
    """
    return description


def save_image_from_base64(image_base64: str, save_path: str) -> str:
    """
    Decode a base64-encoded image and save it to a file.
    
    Args:
        image_base64 (str): The base64-encoded image data.
        save_path (str): The file path to save the image.
    
    Returns:
        str: The path where the image was saved.
    """
    image_bytes: bytes = base64.b64decode(image_base64)
    with open(save_path, "wb") as f:
        f.write(image_bytes)
    return save_path


def get_template_paths() -> Tuple[str, str]:
    """
    Get the paths to the thumbnail template and mask files.
    
    Returns:
        Tuple[str, str]: Paths to template and mask files.
    
    Raises:
        RuntimeError: If template files are not found.
    """
    # Look for template files in the local templates directory
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    
    template_path = template_dir / "thumbnail_template.png"
    mask_path = template_dir / "thumbnail_template_mask.png"
    
    if not template_path.exists() or not mask_path.exists():
        raise RuntimeError(f"Template files not found in {template_dir}")
    
    return str(template_path), str(mask_path)


def generate_thumbnail(
    video_title: str,
    video_subtitle: str,
    background_color: str,
    icon_descriptions: list,
    video_summary: str,
    output_path: str
) -> None:
    """
    Generate a YouTube thumbnail using OpenAI image editing API with template and mask.
    
    Args:
        video_title (str): The main title for the thumbnail.
        video_subtitle (str): The subtitle for the thumbnail.
        background_color (str): The background color (e.g., 'black', 'white').
        icon_descriptions (list): List of descriptions for the three icons.
        video_summary (str): Brief summary of the video content.
        output_path (str): Path to save the generated thumbnail.
    
    Raises:
        RuntimeError: If template files are not found.
    """
    template_path, mask_path = get_template_paths()
    
    # Build the prompt
    icon_one, icon_two, icon_three = icon_descriptions[0], icon_descriptions[1], icon_descriptions[2]
    prompt = (
        f"A YouTube thumbnail with the title '{video_title}' and subtitle '{video_subtitle}'. "
        f"The background color is {background_color}. It includes three icons with no white circle outlines: "
        f"one representing '{icon_one}', another for '{icon_two}', and the third for '{icon_three}'. "
        f"The overall theme reflects the following video summary: '{video_summary}'. "
        f"The design is eye-catching, vibrant, and optimized for attracting programming and software development viewers on YouTube."
    )
    
    print("Generating thumbnail with template...")
    
    # Open template and mask files
    with open(template_path, "rb") as image_file, open(mask_path, "rb") as mask_file:
        result = client.images.edit(
            model="gpt-image-1",
            prompt=prompt,
            image=image_file,
            mask=mask_file,
            background='opaque',
            output_format='jpeg',
            size="1536x1024",
            quality="high"
        )
    
    # Save the generated image
    image_base64 = result.data[0].b64_json
    save_image_from_base64(image_base64, output_path)
    print(f"Thumbnail saved to {output_path}")


def create_thumbnail_iteratively(video_title: str, video_summary: str, output_path: str) -> None:
    """
    Create a YouTube thumbnail iteratively, allowing user to refine until satisfied.
    
    Args:
        video_title (str): The title of the video.
        video_summary (str): Brief summary of the video content.
        output_path (str): Path to save the final thumbnail.
    """
    print("\n=== Thumbnail Generation ===")
    
    # Collect initial thumbnail parameters from user
    video_subtitle: str = prompt_user("Enter the video subtitle: ")
    background_color: str = prompt_user("Enter the background color (e.g., black, white, blue): ")
    icon_one: str = prompt_user("Enter the description for icon one: ")
    icon_two: str = prompt_user("Enter the description for icon two: ")
    icon_three: str = prompt_user("Enter the description for icon three: ")
    
    icon_descriptions = [icon_one, icon_two, icon_three]
    
    temp_path = output_path.replace(".jpg", "_temp.jpg")
    
    print("Generating initial thumbnail...")
    generate_thumbnail(video_title, video_subtitle, background_color, icon_descriptions, video_summary, temp_path)
    print(f"Initial thumbnail saved as {temp_path}")
    
    iteration: int = 1
    current_path = temp_path
    
    # Iterative editing loop
    while True:
        satisfied: str = prompt_user("Are you happy with the thumbnail? (y/n): ").lower()
        if satisfied == 'y':
            break
        
        print("\nLet's refine the thumbnail. You can modify any of the following:")
        edit_choice: str = prompt_user(
            "What would you like to change?\n"
            "1. Video subtitle\n"
            "2. Background color\n"
            "3. Icon descriptions\n"
            "4. All of the above\n"
            "Enter choice (1-4): "
        ).strip()
        
        # Update based on user choice
        if edit_choice in ['1', '4']:
            video_subtitle = prompt_user(f"Enter new subtitle (current: '{video_subtitle}'): ") or video_subtitle
        if edit_choice in ['2', '4']:
            background_color = prompt_user(f"Enter new background color (current: '{background_color}'): ") or background_color
        if edit_choice in ['3', '4']:
            icon_one = prompt_user(f"Enter new description for icon one (current: '{icon_one}'): ") or icon_one
            icon_two = prompt_user(f"Enter new description for icon two (current: '{icon_two}'): ") or icon_two
            icon_three = prompt_user(f"Enter new description for icon three (current: '{icon_three}'): ") or icon_three
            icon_descriptions = [icon_one, icon_two, icon_three]
        
        next_path: str = output_path.replace(".jpg", f"_iter{iteration}.jpg")
        
        print(f"Generating edited thumbnail (iteration {iteration})...")
        generate_thumbnail(video_title, video_subtitle, background_color, icon_descriptions, video_summary, next_path)
        print(f"Edited thumbnail saved as {next_path}")
        
        current_path = next_path
        iteration += 1
    
    # Rename final thumbnail
    if current_path != output_path:
        os.rename(current_path, output_path)
    
    print(f"Final thumbnail saved as {output_path}")


def cleanup_intermediate_files(project_dir: str) -> None:
    """
    Delete all intermediate files, keeping only chapters.txt, description.txt, and thumbnail.jpg.
    
    Args:
        project_dir (str): The project directory to clean up.
    """
    print("\nCleaning up intermediate files...")
    
    # Files to keep
    keep_files = {"chapters.txt", "description.txt", "thumbnail.jpg"}
    
    # Delete temporary files
    for file in os.listdir(project_dir):
        file_path = os.path.join(project_dir, file)
        if os.path.isfile(file_path) and file not in keep_files:
            # Delete JSON, temp images, etc.
            if file.endswith(('.json', '_temp.jpg', '_iter1.jpg', '_iter2.jpg', '_iter3.jpg', 
                             '_iter4.jpg', '_iter5.jpg', '_iter6.jpg', '_iter7.jpg', 
                             '_iter8.jpg', '_iter9.jpg')):
                os.remove(file_path)
                print(f"Deleted: {file}")
    
    print("Cleanup complete!")


def main() -> None:
    """
    Main function to run the complete YouTube video pipeline.
    
    Generates chapters, description, and thumbnail for a YouTube video from an audio file.
    """
    print("=== YouTube Video Pipeline ===\n")
    
    # Step 1: Get project directory
    project_dir: str = prompt_user("Enter the full path to your project directory: ")
    if not os.path.isdir(project_dir):
        print(f"Error: Directory not found: {project_dir}")
        sys.exit(1)
    
    # Convert to Path object
    project_path: Path = Path(project_dir)
    
    # Step 2: Find audio file
    audio_path: Optional[str] = find_audio_file(project_dir)
    if not audio_path:
        print("Error: audio.m4a file not found in the project directory.")
        sys.exit(1)
    
    print(f"Found audio file: {audio_path}\n")
    
    # Step 3: Transcribe audio
    json_path: Path = transcribe_audio(audio_path, project_path)
    
    # Step 4: Generate chapters
    chapters: str = generate_chapters(json_path)
    chapters_path: str = os.path.join(project_dir, "chapters.txt")
    with open(chapters_path, "w", encoding="utf-8") as f:
        f.write(chapters)
    print(f"Chapters saved to {chapters_path}\n")
    
    # Step 5: Generate video summary for description
    summary: str = generate_video_summary(json_path)
    
    # Step 6: Get GitHub URL from user
    github_url: str = prompt_user("Enter the GitHub repository URL for this project: ")
    
    # Step 7: Generate description
    description: str = generate_description(summary, chapters, github_url)
    description_path: str = os.path.join(project_dir, "description.txt")
    with open(description_path, "w", encoding="utf-8") as f:
        f.write(description)
    print(f"Description saved to {description_path}\n")
    
    # Step 8: Generate thumbnail iteratively
    video_title: str = prompt_user("Enter the video title: ")
    thumbnail_path: str = os.path.join(project_dir, "thumbnail.jpg")
    create_thumbnail_iteratively(video_title, summary, thumbnail_path)
    
    # Step 9: Cleanup intermediate files
    cleanup_intermediate_files(project_dir)
    
    print("\n=== Pipeline Complete! ===")
    print(f"Generated files:")
    print(f"  - {chapters_path}")
    print(f"  - {description_path}")
    print(f"  - {thumbnail_path}")


if __name__ == "__main__":
    main()
