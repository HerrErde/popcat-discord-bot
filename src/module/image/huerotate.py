from io import BytesIO

import numpy as np
import requests
from PIL import Image


def adjust_hue(image, hue_shift):
    image = image.convert("RGB").convert("HSV")
    hue, saturation, value = image.split()

    hue = np.array(hue, dtype=np.float32)
    hue = (hue + hue_shift) % 255
    hue = Image.fromarray(hue.astype(np.uint8))

    return Image.merge("HSV", (hue, saturation, value)).convert("RGB")


def create(image_url, degree):
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content)).convert("RGBA")

        # Calculate hue shift
        hue_shift = degree * 255 / 360

        # Adjust hue
        adjusted_image = adjust_hue(image, hue_shift)

        output_bytes = BytesIO()
        adjusted_image.save(output_bytes, format="PNG")
        output_bytes.seek(0)

        return output_bytes
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
