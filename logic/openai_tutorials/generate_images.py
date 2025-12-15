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

# ! Generate an image from a text prompt (Image API)
prompt = "A fantasy style landscape with mountains and a river, vibrant colors, highly detailed"
result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)
with open("./llm_images/landscape.png", "wb") as f:
    f.write(image_bytes)

# Generate an image from a text prompt (Responses API)
# response = client.responses.create(
#     model="gpt-4o",
#     input="Generate an image of a squirrel playing soccer with his friends in a park.",
#     tools=[{"type": "image_generation"}],
# )
# image_data = [
#     output.result
#     for output in response.output
#     if output.type == "image_generation_call"
# ]   
# image_base64 = image_data[0]
# with open("./llm_images/landscape.png", "wb") as f:
#     f.write(base64.b64decode(image_base64))





