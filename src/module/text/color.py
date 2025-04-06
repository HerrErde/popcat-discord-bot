import json

ntc_path = "assets/data/ntc.json"


def get_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r, g, b


def lighten_color(col, amt):
    num = int(col, 16)
    r = (num >> 16) + amt
    b = ((num >> 8) & 0x00FF) + amt
    g = (num & 0x0000FF) + amt
    new_color = (g | (b << 8) | (r << 16)) & 0xFFFFFF
    return hex(new_color)[2:].zfill(6)


def get_color_name(hex_color):
    hex_color = hex_color.upper()
    with open(ntc_path, "r", encoding="utf-8") as file:
        color_data = json.load(file)
        for color_entry in color_data:
            if hex_color in color_entry:
                return color_entry[hex_color]
    return f"Invalid Color: {hex_color}"


def info(hex_color):
    # Convert RGB tuple to RGB string
    get_rgb(hex_color)

    color_name = get_color_name(hex_color)

    brightened = lighten_color(hex_color, 50)

    return (
        f"#{hex_color}",
        color_name,
        str(f"#{brightened}"),
    )
