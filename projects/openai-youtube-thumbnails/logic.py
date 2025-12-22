import base64
import os

from openai import OpenAI

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

template_path = "./templates/thumbnail_template.png"
mask_path = "./templates/thumbnail_template_mask.png"

with open(template_path, "rb") as image_file, open(mask_path, "rb") as mask_file:
    video_title = input("Enter the video title: ")
    video_subtitle = input("Enter the video subtitle: ")
    background_color = input("Enter the background color (e.g., black, white): ")
    icon_one_description = input("Enter the description for icon one: ")
    icon_two_description = input("Enter the description for icon two: ")
    icon_three_description = input("Enter the description for icon three: ")
    video_summary = input("Enter a brief summary of the video content: ")
    
    print("-------------------------------- Generating Thumbnail -------------------------------")
    result = client.images.edit(
        model="gpt-image-1",
        prompt=f"A YouTube thumbnail with the title '{video_title}' and subtitle '{video_subtitle}'. The background color is {background_color}. It includes three icons: one representing '{icon_one_description}', another for '{icon_two_description}', and the third for '{icon_three_description}'. The overall theme reflects the following video summary: '{video_summary}'. The design is eye-catching, vibrant, and optimized for attracting programming and software development viewers on YouTube.",
        image=image_file,
        mask=mask_file,
        background='opaque',
        output_format='jpeg',
        size="1536x1024"
    )
    print("-------------------------------- Thumbnail Generated -------------------------------")

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)
output_path = "./llm_images/youtube_thumbnail.jpg"
with open(output_path, "wb") as f:
    print("-------------------------------- Saving Thumbnail -------------------------------")
    f.write(image_bytes)

print(f"Thumbnail saved to {output_path}")