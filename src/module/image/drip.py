from io import BytesIO

import requests
from PIL import Image

bg_image_path = "assets/images/drip.png"
# Define the region to crop and overlay the image
crop_region = (330, 135, 555, 360)
output_width = (
    crop_region[2] - crop_region[0]
)  # Calculate the width of the output image
output_height = (
    crop_region[3] - crop_region[1]
)  # Calculate the height of the output image


def create(image):
    try:

        response = requests.get(image)
        image = Image.open(BytesIO(response.content))

        image = image.resize((output_width, output_height))

        bg_image = Image.open(bg_image_path)
        bg_image = bg_image.convert("RGBA")

        output_image = Image.new("RGBA", bg_image.size)

        output_image.paste(image, crop_region)

        output_image.paste(bg_image, (0, 0), bg_image)

        output_bytes = BytesIO()
        output_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
