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
        im = Image.open(BytesIO(response.content)).convert(
            "RGBA"
        )  # Ensure the image is in RGBA mode
        im = im.resize(
            (275, 275), Image.LANCZOS
        )  # Use LANCZOS for higher quality resizing

        overlay = Image.open("triggered.png").convert("RGBA")
        overlay_size = (overlay.width + 5, overlay.height + 5)
        overlay = overlay.resize(
            overlay_size, Image.LANCZOS
        )  # Use LANCZOS for higher quality resizing
        ml = []

        for _ in range(10):
            blank = Image.new("RGBA", (256, 310), (0, 0, 0, 0))

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

        # Reduce the number of colors to further optimize the GIF size
        ml = [frame.quantize(colors=512, method=Image.FASTOCTREE) for frame in ml]

        duration = 20

        output_bytes = BytesIO()
        ml[0].save(
            output_bytes,
            format="GIF",
            save_all=True,
            loop=0,
            append_images=ml[1:],
            duration=duration,
            optimize=True,  # Optimize the GIF to reduce size
        )

        output_bytes.seek(0)  # Rewind the file pointer to the start of the stream
        return output_bytes.getvalue()
    except Exception as e:
        print(f"Error creating triggered image: {e}")
        return None


image_url = "https://cdn.discordapp.com/avatars/517030982507823105/4ad25bb3b90740c53572177ffbd8c8a3.png"
gif_data = create(image_url)

# Save the result to a file for verification
with open("output.gif", "wb") as f:
    f.write(gif_data)
