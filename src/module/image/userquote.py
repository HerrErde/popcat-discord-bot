from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

font_path = "assets/font/moskau-grotesk-bold.otf"
width = 1080
height = 1080
text1_position = (460, 870)
text2_position = (460, 950)


def get_text_size(text, font):
    im = Image.new(mode="RGB", size=(1, 1))
    draw = ImageDraw.Draw(im)
    return draw.textbbox((0, 0), text=text, font=font)[2:]


def create(text, image, name):
    try:
        response_bg = requests.get(image)
        response_bg.raise_for_status()
        bg_image = Image.open(BytesIO(response_bg.content))
        bg_image = bg_image.resize((width, height))

        composite_image = Image.new("RGBA", (width, height))

        composite_image.paste(bg_image, (0, 0))

        # Create a gradient overlay
        gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_gradient = ImageDraw.Draw(gradient)

        start_y = 0
        end_y = height

        # Draw the gradient from black to transparent with reduced opacity
        for y in range(start_y, end_y):
            alpha = int(130 * (y - start_y) / (end_y - start_y))
            draw_gradient.line([(0, y), (width, y)], fill=(0, 0, 0, alpha), width=1)

        composite_image = Image.alpha_composite(composite_image, gradient)

        draw = ImageDraw.Draw(composite_image)
        font1 = ImageFont.truetype(font_path, 62)
        font2 = ImageFont.truetype(font_path, 42)

        draw.text(text1_position, f'"{text}"', font=font1, fill="white")
        draw.text(text2_position, f"- {name}", font=font2, fill="#cdd2e4")

        output_bytes = BytesIO()
        composite_image.convert("RGB").save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
