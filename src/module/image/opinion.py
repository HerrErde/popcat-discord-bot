from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

bg_image_path = "assets/images/opinion.png"
text_position = (100, 435)
font_path = "assets/font/arial.ttf"
text_color = (0, 0, 0)
font_size = 35
line_spacing = 5

crop1_region = (100, 502, 222, 624)
crop2_region = (386, 263, 492, 370)
output1_width = crop1_region[2] - crop1_region[0]
output1_height = crop1_region[3] - crop1_region[1]
output2_width = crop2_region[2] - crop2_region[0]
output2_height = crop2_region[3] - crop2_region[1]


def textsize(text, font):
    im = Image.new(mode="RGB", size=(1, 1))
    draw = ImageDraw.Draw(im)
    width, height = draw.textbbox((0, 0), text=text, font=font)[2:]
    return width, height


def create(text, image_url):
    try:

        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

        image1 = image.resize((output1_width, output1_height))
        image2 = image.resize((output2_width, output2_height))

        bg_image = Image.open(bg_image_path).convert("RGBA")

        output_image = Image.new("RGBA", bg_image.size)

        # Paste the resized images onto the background image at the specified crop regions
        output_image.paste(image1, crop1_region[:2])
        output_image.paste(image2, crop2_region[:2])

        # Paste the background image onto the transparent image (covering the resized images)
        output_image.paste(bg_image, (0, 0), bg_image)

        draw = ImageDraw.Draw(output_image)

        font = ImageFont.truetype(font_path, size=font_size)

        # Calculate maximum text width to prevent text overflow
        max_text_width = crop2_region[2] - crop1_region[0]

        def draw_text(draw, text, position, font, color, max_width):
            lines = []
            words = text.split()
            while words:
                line = ""
                while words and textsize(line + words[0], font)[0] <= max_width:
                    line += words.pop(0) + " "
                lines.append(line)
            y = position[1]
            for line in lines:
                draw.text((position[0], y), line, font=font, fill=color)
                y += textsize(line, font)[1] + line_spacing

        draw_text(draw, text, text_position, font, text_color, max_text_width)

        output_bytes = BytesIO()
        output_image.save(output_bytes, format="PNG")

        return output_bytes.getvalue()

    except Exception as e:
        print(f"Error creating image: {e}")
        return None
