from io import BytesIO

import requests
from PIL import Image

bg_image_path = "assets/images/whowouldwin.png"


def create(image1, image2):
    try:

        response1 = requests.get(image1)
        response2 = requests.get(image2)
        image1 = Image.open(BytesIO(response1.content))
        image2 = Image.open(BytesIO(response2.content))

        bg_image = Image.open(bg_image_path).convert("RGBA")

        region1 = (41, 124, 358, 448)
        region2 = (461, 124, 778, 448)

        output_image = Image.new("RGBA", bg_image.size)

        # Paste the background image onto the transparent image
        output_image.paste(bg_image, (0, 0), bg_image)

        output_image.paste(
            image1.resize((region1[2] - region1[0], region1[3] - region1[1])),
            region1[:2],
        )
        output_image.paste(
            image2.resize((region2[2] - region2[0], region2[3] - region2[1])),
            region2[:2],
        )

        output_bytes = BytesIO()
        output_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
