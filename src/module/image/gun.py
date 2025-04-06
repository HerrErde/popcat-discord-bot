from io import BytesIO

import requests
from PIL import Image

bg_image_path = "assets/images/gun.png"


def create(image_url):
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

        bg_image = Image.open(bg_image_path).convert("RGBA")

        # Resize the image to match the dimensions of the background image
        image = image.resize(bg_image.size)

        output_image = Image.new("RGBA", bg_image.size)

        # Paste the resized image onto the transparent image
        output_image.paste(image, (0, 0), image)
        # Paste the background image onto the transparent image
        output_image.paste(bg_image, (0, 0), bg_image)

        output_bytes = BytesIO()
        output_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
