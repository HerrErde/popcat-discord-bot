import random
from io import BytesIO
import requests
from PIL import Image


def apply_red_tint(image, tint_color):
    """Apply a red tint to the image."""
    tint_image = Image.new("RGBA", image.size, tint_color)
    tinted_image = Image.blend(image, tint_image, alpha=tint_color[3] / 255.0)
    return tinted_image


def create(image_url):
    try:
        response = requests.get(image_url)
        im = Image.open(BytesIO(response.content)).convert("RGBA")
        im = im.resize((275, 750), Image.BILINEAR)

        overlay = Image.open("assets/images/triggered.png").convert("RGBA")
        overlay_size = (overlay.width + 5, overlay.height + 5)
        overlay = overlay.resize(overlay_size, Image.BILINEAR)
        ml = []

        for _ in range(10):
            blank = Image.new("RGBA", (256, 310))

            # Center position for the main image
            center_x = (blank.width - im.width) // 2
            center_y = (blank.height - im.height) // 2
            center_y += -25

            # Apply a random offset to the centered image
            x_im = center_x + random.randint(-7, 7)
            y_im = center_y + random.randint(-7, 7)
            blank.paste(im, (x_im, y_im), im)

            # Apply red tint
            blank = apply_red_tint(blank, (255, 0, 0, 50))

            x_overlay = (blank.width - im.width) // 2
            y_overlay = (blank.height - im.height) // 2
            x_overlay += 6
            y_overlay += -16

            # Random position for the overlay
            x_overlay = x_overlay + random.randint(-2, 2)
            y_overlay = y_overlay + random.randint(-4, 4)
            blank.paste(overlay, (x_overlay, y_overlay), overlay)

            ml.append(blank)

        duration = 20

        output_bytes = BytesIO()
        ml[0].save(
            output_bytes,
            format="GIF",
            save_all=True,
            loop=0,
            append_images=ml[1:],
            duration=duration,
        )

        return output_bytes.getvalue()
    except Exception as e:
        print(f"Error creating triggered image: {e}")
        return None
