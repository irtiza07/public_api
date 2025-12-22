# Iterative OpenAI Image Generation and Editing Script

# Iterative OpenAI Image Generation and Editing Script (using OpenAI client pattern)


import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional

# Load environment and OpenAI client at the top

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
	return input(prompt)



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



# Use Responses API for both initial and iterative image generation

def generate_or_edit_image(
	prompt: str,
	out_path: str,
	previous_response_id: Optional[str] = None
) -> str:
	"""
	Generate a new image or edit an existing one using the OpenAI Responses API.
	Args:
		prompt (str): The prompt or edit instructions for image generation.
		out_path (str): The file path to save the generated image.
		previous_response_id (Optional[str]): The response ID from a previous generation for iterative editing.
	Returns:
		str: The response ID of the current image generation, for further iterations.
	Raises:
		RuntimeError: If no image is generated in the response.
	"""
	# If previous_response_id is provided, pass it to the responses API for iterative edits
	response = client.responses.create(
		model="gpt-5",
		input=prompt,
		tools=[{"type": "image_generation"}],
		previous_response_id=previous_response_id
	)
	# Find the image output in the response
	image_data = [output.result for output in response.output if output.type == "image_generation_call"]
	if not image_data:
		raise RuntimeError("No image generated in response.")
	image_base64: str = image_data[0]
	save_image_from_base64(image_base64, out_path)
	return response.id  # Return response id for next context





def main() -> None:
	"""
	Main function to run the iterative image generation and editing workflow.
	Prompts the user for an initial image description, generates the image, and allows iterative edits until the user is satisfied.
	The final image is saved with a '_final' suffix.
	"""
	# 1. Prompt user for initial description
	initial_prompt: str = prompt_user("Enter a description for the image you want to generate: ")
	base_filename: str = "generated_image"
	original_path: str = f"{base_filename}_original.png"

	# 2. Generate and save original image using Responses API
	print("Generating original image...")
	response_id: str = generate_or_edit_image(initial_prompt, original_path)
	print(f"Original image saved as {original_path}")

	current_path: str = original_path
	iteration: int = 1
	previous_response_id: str = response_id

	# 3. Iterative editing loop using previous_response_id
	while True:
		satisfied: str = prompt_user("Are you happy with the image? (y/n): ").strip().lower()
		if satisfied == 'y':
			break
		edit_prompt: str = prompt_user("Describe the edits or new prompt for the next iteration: ")
		next_path: str = f"{base_filename}_iter{iteration}.png"
		print(f"Generating edited image (iteration {iteration})...")
		previous_response_id = generate_or_edit_image(edit_prompt, next_path, previous_response_id=previous_response_id)
		print(f"Edited image saved as {next_path}")
		current_path = next_path
		iteration += 1

	# 4. Save final image with '_final' suffix
	final_path: str = f"{base_filename}_final.png"
	os.rename(current_path, final_path)
	print(f"Final image saved as {final_path}")

if __name__ == "__main__":
	main()
