import math
import random
from io import BytesIO

import requests
from PIL import Image


def create(avatar_url, level, num_waves=5):

    response_image = requests.get(avatar_url)
    img = Image.open(BytesIO(response_image.content)).convert("RGBA")

    width, height = img.size
    pixels = img.load()

    new_img = Image.new("RGB", (width, height))
    new_pixels = new_img.load()

    # Generate random wave parameters
    wave_params = []
    for _ in range(num_waves):
        amplitude_x = random.uniform(-level, level)
        frequency_x = random.uniform(1, 10)
        phase_shift_x = random.uniform(0, 2 * math.pi)

        amplitude_y = random.uniform(-level, level)
        frequency_y = random.uniform(1, 10)
        phase_shift_y = random.uniform(0, 2 * math.pi)

        wave_params.append(
            (
                amplitude_x,
                frequency_x,
                phase_shift_x,
                amplitude_y,
                frequency_y,
                phase_shift_y,
            )
        )

    # Apply wave effect
    for y in range(height):
        for x in range(width):
            new_x, new_y = x, y
            for (
                amplitude_x,
                frequency_x,
                phase_shift_x,
                amplitude_y,
                frequency_y,
                phase_shift_y,
            ) in wave_params:
                new_x += amplitude_x * math.sin(
                    frequency_x * y / height * 2 * math.pi + phase_shift_x
                )
                new_y += amplitude_y * math.sin(
                    frequency_y * x / width * 2 * math.pi + phase_shift_y
                )

            new_x, new_y = int(new_x), int(new_y)

            if 0 <= new_x < width and 0 <= new_y < height:
                new_pixels[x, y] = pixels[new_x, new_y]
            else:
                new_pixels[x, y] = (0, 0, 0)

    output_bytes = BytesIO()
    new_img.save(output_bytes, format="PNG")
    output_bytes.seek(0)
    return output_bytes
