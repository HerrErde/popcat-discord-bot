from io import BytesIO

import requests
from PIL import Image


def create(user1, user2, alpha=0.7):
    try:

        response1 = requests.get(user1)
        response2 = requests.get(user2)
        image1 = Image.open(BytesIO(response1.content))
        image2 = Image.open(BytesIO(response2.content))

        # Ensure both images are in the same mode (convert to RGBA)
        image1 = image1.convert("RGBA")
        image2 = image2.convert("RGBA")

        # Ensure both images have the same size
        if image1.size != image2.size:
            image2 = image2.resize(image1.size, Image.LANCZOS)

        # Blend the images with the given alpha for transparency
        blended_image = Image.blend(image1, image2, alpha)

        output_bytes = BytesIO()
        blended_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
