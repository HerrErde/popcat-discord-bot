from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

bg_image_path = "assets/images/pooh.png"
text1_position = (380, 45)
text2_position = (380, 340)
font_path = "assets/font/arial.ttf"
text_color = (0, 0, 0)
max_text_width = 400
font_size = 40
line_spacing = 5


def textsize(text, font):
    im = Image.new(mode="RGB", size=(1, 1))
    draw = ImageDraw.Draw(im)
    width, height = draw.textbbox((0, 0), text=text, font=font)[2:]
    return width, height


def wrap_text(text, font, max_width):
    """Wrap text to fit within a maximum width."""
    lines = []
    words = text.split()
    if not words:
        return lines

    current_line = words[0]
    for word in words[1:]:
        test_line = current_line + " " + word
        width, _ = textsize(test_line, font)
        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    return lines


def draw_wrapped_text(
    draw, text, position, font, text_color, max_width, line_spacing=5
):
    """Draw wrapped text on an image using specified parameters."""
    lines = wrap_text(text, font, max_width)
    y = position[1]
    for line in lines:
        text_width, text_height = textsize(line, font)
        x = position[0] - text_width / 2
        draw.text((x, y), line, font=font, fill=text_color)
        y += text_height + line_spacing


def create(text1, text2):
    try:

        bg_image = Image.open(bg_image_path)
        bg_image = bg_image.convert("RGBA")

        draw = ImageDraw.Draw(bg_image)

        font = ImageFont.truetype(font_path, size=font_size)

        draw_wrapped_text(
            draw, text1, text1_position, font, text_color, max_text_width, line_spacing
        )
        draw_wrapped_text(
            draw, text2, text2_position, font, text_color, max_text_width, line_spacing
        )

        output_bytes = BytesIO()
        bg_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
