import re
from io import BytesIO

import requests
from PIL import Image


def correct_hex_code(hex_code):
    # Remove any non-hex characters
    hex_code = re.sub(r"[^a-fA-F0-9]", "", hex_code)

    # If the code is too short, pad it with zeros; if too long, truncate it
    if len(hex_code) < 6:
        hex_code = hex_code.ljust(6, "0")
    elif len(hex_code) > 6:
        hex_code = hex_code[:6]

    return hex_code


def hex_to_rgb(hex_code):
    hex_code = correct_hex_code(hex_code)
    return tuple(int(hex_code[i : i + 2], 16) for i in range(0, 6, 2))


def blend_colors(color1, color2, blend_factor):
    return tuple(
        int(color1[i] * (1 - blend_factor) + color2[i] * blend_factor) for i in range(3)
    )


def create(image_url, hex_color):
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content)).convert("RGBA")

        tint_color = hex_to_rgb(hex_color)

        tinted_image = Image.new("RGBA", image.size)

        # Get image data
        pixels = image.load()
        tinted_pixels = tinted_image.load()

        for i in range(image.width):
            for j in range(image.height):
                r, g, b, a = pixels[i, j]

                # Determine the intensity of the pixel
                intensity = (r + g + b) / 3

                # Normalize intensity to a range of 0 to 1
                blend_factor = 1 - (intensity / 255)

                # Blend the tint color with the original color based on intensity
                blended_color = blend_colors((r, g, b), tint_color, blend_factor)
                tinted_pixels[i, j] = (*blended_color, a)

        output_bytes = BytesIO()
        tinted_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
