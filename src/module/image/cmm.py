from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

bg_image_path = "assets/images/cmm.png"
text_position = (500, 600)
font_path = "assets/font/arial.ttf"
rotation_angle = 21
font_size = 40


def textsize(text, font):
    im = Image.new(mode="RGB", size=(1, 1))
    draw = ImageDraw.Draw(im)
    width, height = draw.textbbox((0, 0), text=text, font=font)[2:]
    return width, height


def create(text):
    try:
        bg_image = Image.open(bg_image_path).convert("RGBA")

        custom_font = ImageFont.truetype(font_path, size=font_size)

        ImageDraw.Draw(bg_image)

        text_color = (0, 0, 0)

        # Calculate text dimensions using textsize function
        text_width, text_height = textsize(text, font=custom_font)

        # Rotate the text
        rotated_text = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
        draw_rotated = ImageDraw.Draw(rotated_text)
        draw_rotated.text((0, 0), text, font=custom_font, fill=text_color)

        rotated_text = rotated_text.rotate(rotation_angle, expand=True)

        # Calculate the position to paste the rotated text on the background image
        paste_position = (
            text_position[0] - rotated_text.width // 2,
            text_position[1] - rotated_text.height // 2,
        )

        # Paste the rotated text onto the background image
        bg_image.paste(rotated_text, paste_position, rotated_text)

        output_bytes = BytesIO()
        bg_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
