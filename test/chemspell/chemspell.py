import json
import os
from itertools import product

from PIL import Image, ImageDraw, ImageFont


def textsize(text, font):
    im = Image.new(mode="RGB", size=(1, 1))
    draw = ImageDraw.Draw(im)
    return draw.textbbox((0, 0), text=text, font=font)[2:]


json_path = "PeriodicTableJSON.json"
if not os.path.exists(json_path):
    print(f"JSON file '{json_path}' not found.")
    exit()

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

elements = data["elements"]
element_dict = {el["symbol"]: el for el in elements}


# Function to create images for each element
def create_image(symbol, name, color, background_color=(255, 255, 255)):
    # Convert hex color to RGB if needed
    if color is not None and len(color) == 6:
        color = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    img = Image.new("RGB", (132, 143), color=background_color)
    d = ImageDraw.Draw(img)

    # Define font and size
    try:
        font_symbol = ImageFont.truetype("arial.ttf", 50)
        font_name = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        print("Font file 'arial.ttf' not found.")
        return img

    # Calculate text size and position for the symbol
    text_width, text_height = textsize(symbol, font=font_symbol)
    position_symbol = ((132 - text_width) / 2, (143 - text_height) / 2 - 20)

    # Calculate text size and position for the name
    text_width, text_height = textsize(name, font=font_name)
    position_name = ((132 - text_width) / 2, (143 - text_height) / 2 + 20)

    # Add text to image
    d.text(position_symbol, symbol, fill=(0, 0, 0), font=font_symbol)
    d.text(position_name, name, fill=(0, 0, 0), font=font_name)

    return img


def find_elements(word):
    element_set = set(element_dict.keys())

    def find_elements_recursive(remaining_word, current_path):
        if not remaining_word:
            return current_path

        for i in range(1, 3):
            if remaining_word[:i].capitalize() in element_set:
                result = find_elements_recursive(
                    remaining_word[i:], current_path + [remaining_word[:i].capitalize()]
                )
                if result:
                    return result
        return None

    return find_elements_recursive(word, [])


def get_combinations(word):
    elements_list = find_elements(word)
    if not elements_list:
        return 0
    return len(list(product(*[element_dict[symbol] for symbol in elements_list])))


def spell(word="amogus"):
    combinations_count = get_combinations(word)
    print(f"Number of combinations to create '{word}': {combinations_count}")

    elements_list = find_elements(word)
    if not elements_list:
        print("Cannot spell this word with element symbols")
        return

    print(
        f"'{word}' => {' => '.join(elements_list)} ({', '.join(element_dict[s]['name'] for s in elements_list)})"
    )

    images = []
    for symbol in elements_list:
        element = element_dict.get(symbol)
        if element:
            img = create_image(
                element["symbol"], element["name"], element.get("cpk-hex", None)
            )
            images.append(img)

    # Calculate the size of the final image
    width = len(images) * 132
    height = 143

    final_img = Image.new("RGB", (width, height), color=(255, 255, 255))

    # Paste each image onto the final image
    x_offset = 0
    for img in images:
        final_img.paste(img, (x_offset, 0))
        x_offset += 132

    # Save the final image
    final_img.save("final_image.png")


spell()
