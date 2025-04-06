import json
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

json_path = "PeriodicTableJSON.json"
font_path = "arial.ttf"


def textbbox(text, font):
    im = Image.new(mode="RGB", size=(1, 1))
    draw = ImageDraw.Draw(im)
    bbox = draw.textbbox((0, 0), text=text, font=font)
    width, height = (
        bbox[2] - bbox[0],
        bbox[3] - bbox[1],
    )  # Calculate width and height from bounding box
    return width, height


def find_elements(word, element_dict):
    element_set = set(element_dict.keys())
    length = len(word)
    all_combinations = []

    def backtrack(start_index, path):
        if start_index == length:
            all_combinations.append(path[:])
            return

        for i in range(
            start_index + 1, min(start_index + 3, length + 1)
        ):  # Check symbols of length 1 to 2
            candidate = word[start_index:i].capitalize()
            if candidate in element_set:
                backtrack(i, path + [candidate])

    backtrack(0, [])
    return all_combinations


def create(elements_list, element_dict):
    if not elements_list:
        print("Cannot spell this word with element symbols")
        return None

    img = Image.new(
        "RGB", (200 * len(elements_list), 200), color=(242, 212, 252)
    )  # Light purple background
    d = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_symbol = ImageFont.truetype(font_path, 90)
        font_name = ImageFont.truetype(font_path, 30)
    except IOError:
        font_symbol = ImageFont.load_default()
        font_name = ImageFont.load_default()

    x_offset = 0  # Initial x offset for placing symbols and names

    for symbol in elements_list:
        element = element_dict[symbol]

        # Calculate text size and position for the symbol
        text_width, text_height = textbbox(symbol, font=font_symbol)
        position_symbol = ((200 - text_width) / 2, (200 - text_height) / 2 - 30)

        # Calculate text size and position for the name
        text_width, text_height = textbbox(element["name"], font=font_name)
        position_name = ((200 - text_width) / 2, (200 - text_height) / 2 + 60)

        text_width, text_height = textbbox(str(element["number"]), font=font_name)
        position_number = ((325 - text_width) / 2, (35 - text_height) / 2 + 10)

        # Draw a border around the element with increased thickness
        border_width = 5
        border_space = 5
        rect_start = (x_offset + border_space, border_space)
        rect_end = (x_offset + 200 - border_space, 200 - border_space)
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

        x_offset += 200  # Increase x_offset for the next element

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


# Example usage:
word_to_spell = "os"
image_bytes, combination_count, spelled_word, elements_used = spell(word_to_spell)
if image_bytes:
    with open("output.png", "wb") as f:
        f.write(image_bytes)
    print(f"Spelled word: {spelled_word}")
    print(f"Elements used: {elements_used}")
    print(f"Number of combinations: {combination_count}")
else:
    print("Cannot spell this word with element symbols")
