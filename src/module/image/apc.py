from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

width = 800
height = 400

bg_img_path = "assets/images/paper.png"
font_path = "assets/font/EBGaramond-Regular.ttf"
font_medium_path = "assets/font/Cormorant-Medium.otf"

text_color = "#323232"  # Black

name = "Patric Bateman"
title = "Vice President"
phone = "212 555 6342"
logo = "Pierce & Pierce"
tagline = "Mergers and Acquisitions"
address = "358 Exchange Place New York, N.Y. 10099 fax 212 555 6390 telex 10 4534"

name_pos = (400, 183)
title_pos = (400, 225)
phone_pos = (112, 60)
logo_pos = (675, 60)
tagline_pos = (635, 85)
address_pos = (400, 370)


def draw_centered_text(draw, position, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = position[0] - text_width // 2
    text_y = position[1] - text_height // 2
    draw.text((text_x, text_y), text, font=font, fill=fill)


def draw_text(draw, name, title, phone, logo, tagline, address):
    name_font = ImageFont.truetype(font_path, size=22)
    title_font = ImageFont.truetype(font_path, size=22)
    phone_font = ImageFont.truetype(font_path, size=32)
    logo_font = ImageFont.truetype(font_medium_path, size=25)
    tagline_font = ImageFont.truetype(font_medium_path, size=18)
    address_font = ImageFont.truetype(font_path, size=23)

    draw_centered_text(draw, name_pos, name.upper(), name_font, text_color)
    draw_centered_text(draw, title_pos, title.upper(), title_font, text_color)
    draw_centered_text(draw, phone_pos, phone, phone_font, text_color)
    draw_centered_text(draw, logo_pos, logo, logo_font, text_color)
    draw_centered_text(draw, tagline_pos, tagline.upper(), tagline_font, text_color)
    draw_centered_text(draw, address_pos, address, address_font, text_color)


def create(name, title, logo, tagline):

    background_color = "#f9f9ef"
    image = Image.new("RGB", (width, height), background_color)

    background_image = Image.open(bg_img_path).convert("RGBA")
    bg_width, bg_height = background_image.size

    alpha_mask = background_image.split()[3]

    # Paste and repeat the background image over the new image with the alpha mask
    for i in range(0, width, bg_width):
        for j in range(0, height, bg_height):
            # Calculate the paste position considering the image boundaries
            paste_x = i
            paste_y = j

            # Determine the paste size within boundaries
            paste_width = min(bg_width, width - paste_x)
            paste_height = min(bg_height, height - paste_y)

            # Paste the background image portion onto the base image using the alpha mask
            image.paste(
                background_image.crop((0, 0, paste_width, paste_height)),
                (paste_x, paste_y),
                mask=alpha_mask.crop((0, 0, paste_width, paste_height)),
            )

    draw = ImageDraw.Draw(image)

    draw_text(draw, name, title, phone, logo, tagline, address)

    output_bytes = BytesIO()
    image.save(output_bytes, format="PNG")

    return output_bytes.getvalue()
