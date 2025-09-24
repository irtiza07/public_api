import os

from openai import OpenAI

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# TWO APPROACHES - (1) Photo URLs (2) Base64 encoded images

# POKEMON IMAGE URLS
BULBASAUR_IMAGE_URL = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/001.png"
SQUIRTLE_IMAGE_URL = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/007.png"
PIKACHU_IMAGE_URL = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/025.png"
ARCANINE_IMAGE_URL = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/059.png"
ZAPDOS_IMAGE_URL = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/145.png"
CYNDAQUIL_IMAGE_URL = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/155.png"
MUDKIP_IMAGE_URL = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/258.png"
CARD_URL = "https://images.unsplash.com/photo-1628968434441-d9c1c66dcde7?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"

# PEOPLE IMAGE URLS
GROUP_PHOTO_URL = "https://images.unsplash.com/photo-1625283518288-00362afc8663?q=80&w=985&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
MANY_PEOPLE_PHOTO_URL = "https://images.unsplash.com/photo-1656370465119-cb8d6735bda3?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"

# LOCATION IMAGE URLS
ISTANBUL_URL = "https://plus.unsplash.com/premium_photo-1691338312403-e9f7f7984eeb?q=80&w=1064&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
BRAZIL_URL = "https://images.unsplash.com/photo-1551620832-e2af54f6f0b8?q=80&w=987&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
DHAKA_URL = "https://images.unsplash.com/photo-1716465107914-95393516e40f?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
SMOKY_MOUNTAIN_NATIONAL_PARK_URL = "https://images.unsplash.com/photo-1691178619046-566795fc8a75?q=80&w=2988&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
RANDOM_LOCATION = "https://lh3.googleusercontent.com/pw/AP1GczMR8yZiwX07Hz3BwESjFmWNsoexHWYbeTs3A7jrnASyefyoPjSkzF-ioJhvmXakIZ8VeMNVAPPFYYHpdePq6SWs6iK3616a36IRl3g40TNkmNoEQjK3W7bLnTpMzDX5RmgCURGjesyvvPxd-zpjYyEzOA=w2176-h1638-s-no-gm?authuser=0"

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


response = client.responses.create(
    model="gpt-5",  # Try gpt-5 when more inference required
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Identify all unique pokemon from their cards. For each Pokemon, list one attack move visible on the card.",
                },
                {
                    "type": "input_image",
                    "image_url": f"{CARD_URL}",
                },
            ],
        },
    ],
)

print(response.output_text)
