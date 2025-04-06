from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

bg_image_path = "assets/images/biden.png"
text_position = (20, 105)
font_path = "assets/font/segoe_ui.ttf"


def create(text):
    try:
        bg_image = Image.open(bg_image_path)
        bg_image = bg_image.convert("RGBA")

        draw = ImageDraw.Draw(bg_image)

        custom_font = ImageFont.truetype(font_path, size=31)

        text_color = (0, 0, 0)

        draw.text(text_position, text, fill=text_color, font=custom_font)

        output_bytes = BytesIO()
        bg_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
