import random
from PIL import Image


def apply_red_tint(image, tint_color):
    """Apply a red tint to the image."""
    tint_image = Image.new("RGBA", image.size, tint_color)
    tinted_image = Image.blend(image, tint_image, alpha=tint_color[3] / 255.0)
    return tinted_image


def triggered(input_image_path: str, output_gif_path: str) -> None:
    im = Image.open(input_image_path)
    im = im.resize((500, 500), Image.BILINEAR)
    overlay = Image.open("triggered.png")
    ml = []

    for _ in range(10):
        blank = Image.new("RGBA", (400, 400))

        # Random position for the main image
        x_im = -1 * (random.randint(50, 80))
        y_im = -1 * (random.randint(50, 80))
        blank.paste(im, (x_im, y_im))

        # Apply red tint
        blank = apply_red_tint(blank, (255, 0, 0, 80))

        # Random position for the overlay
        x_overlay = random.randint(-4, 4)
        y_overlay = random.randint(-4, 4)
        blank.paste(overlay, (x_overlay, y_overlay), overlay)

        ml.append(blank)

    duration = 20

    ml[0].save(
        output_gif_path,
        format="GIF",
        save_all=True,
        loop=0,
        append_images=ml,
        duration=duration,
    )


# Example usage
input_image_path = "avatar.png"
output_gif_path = "output.gif"
triggered(input_image_path, output_gif_path)
