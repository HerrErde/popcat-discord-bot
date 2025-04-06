import json
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

json_path = "assets/data/PeriodicTableJSON.json"
font_path = "assets/font/arial.ttf"


def textsize(text, font):
    im = Image.new(mode="RGB", size=(1, 1))
    draw = ImageDraw.Draw(im)
    width, height = draw.textbbox((0, 0), text=text, font=font)[2:]
    return width, height


# Function to find elements in a word
def find_elements(word, element_dict):
    element_set = set(element_dict.keys())
    all_combinations = []

    def find_elements_recursive(remaining_word, current_path):
        if not remaining_word:
            all_combinations.append(current_path)
            return

        for i in range(1, min(3, len(remaining_word)) + 1):
            if remaining_word[:i].capitalize() in element_set:
                find_elements_recursive(
                    remaining_word[i:], current_path + [remaining_word[:i].capitalize()]
                )

    find_elements_recursive(word, [])
    return all_combinations


def create(elements_list, element_dict):
    if not elements_list:
        print("Cannot spell this word with element symbols")
        return None

    img = Image.new(
        "RGB", (400 * len(elements_list), 400), color=(242, 212, 252)
    )  # Light purple background
    d = ImageDraw.Draw(img)

    try:
        font_symbol = ImageFont.truetype(font_path, 180)
        font_name = ImageFont.truetype(font_path, 60)
    except IOError:
        font_symbol = ImageFont.load_default()
        font_name = ImageFont.load_default()

    x_offset = 0  # Initial x offset for placing symbols and names

    for index, symbol in enumerate(elements_list, start=1):
        element = element_dict[symbol]

        # Calculate text size and position for the symbol
        text_width, text_height = textsize(symbol, font=font_symbol)
        position_symbol = ((400 - text_width) / 2, (440 - text_height) / 2 - 60)

        # Calculate text size and position for the name
        text_width, text_height = textsize(element["name"], font=font_name)
        position_name = ((400 - text_width) / 2, (400 - text_height) / 2 + 120)

        text_width, text_height = textsize(str(element["number"]), font=font_name)
        position_number = ((650 - text_width) / 2, (70 - text_height) / 2 + 20)

        # Draw a border around the element with increased thickness
        border_width = 10
        border_space = 10
        rect_start = (x_offset + border_space, border_space)
        rect_end = (x_offset + 400 - border_space, 400 - border_space)
        d.rectangle([rect_start, rect_end], outline=(0, 0, 0), width=border_width)

        # Add symbol and name to the composite image
        d.text(
            (x_offset + position_symbol[0], position_symbol[1]),
            symbol,
            fill=(0, 0, 0),
            font=font_symbol,
        )
        d.text(
            (x_offset + position_name[0], position_name[1]),
            element["name"],
            fill=(0, 0, 0),
            font=font_name,
        )
        d.text(
            (x_offset + position_number[0], position_number[1]),
            str(element["number"]),
            fill=(0, 0, 0),
            font=font_name,
        )

        x_offset += 400  # Increase x_offset for the next element

    output_bytes = BytesIO()
    img.save(output_bytes, format="PNG")
    return output_bytes.getvalue()


def spell(word):

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data["elements"]
    element_dict = {el["symbol"]: el for el in elements}

    all_combinations = find_elements(word, element_dict)
    if not all_combinations:
        print("Cannot spell this word with element symbols")
        return None, 0, None, None

    random_combination = random.choice(all_combinations)
    output_bytes = create(random_combination, element_dict)
    amount = len(all_combinations)

    spelled_word = "".join(random_combination).capitalize()
    element_list = [element_dict[symbol]["name"] for symbol in random_combination]

    return output_bytes, amount, spelled_word, element_list
