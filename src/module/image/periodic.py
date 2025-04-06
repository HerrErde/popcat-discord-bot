import json
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

periodic_file_path = "assets/data/PeriodicTableJSON.json"
font_path = "assets/font/Eina01-Bold.ttf"
font_path2 = "assets/font/NeverMind-Bold.ttf"
font_path3 = "assets/font/NeverMind-Regular.ttf"


class Periodic:
    @staticmethod
    def load_periodic_table():
        with open(periodic_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data

    @staticmethod
    def get_element(element):
        elements = Periodic.load_periodic_table()["elements"]

        # Lookup by name, symbol, or atomic number
        for el in elements:
            if (
                el["name"].lower() == element.lower()
                or el["symbol"].lower() == element.lower()
                or str(el["number"]) == element
            ):
                return (
                    el["name"],
                    el["symbol"],
                    el["number"],
                    el["atomic_mass"],
                    el["period"],
                    el["phase"],
                    el["discovered_by"],
                    el["summary"],
                )
        return None

    @staticmethod
    def create(element):
        width, height = 500, 500
        text_color = (242, 194, 1)  # RGB value for #f2c201
        bg_color = (53, 64, 77)  # RGB value for #35404d

        def textsize(text, font):
            im = Image.new(mode="RGB", size=(1, 1))
            draw = ImageDraw.Draw(im)
            width, height = draw.textbbox((0, 0), text=text, font=font)[2:]
            return width, height

        def draw_square(draw):
            square_color = text_color
            # (x0, y0, x1, y1) for the rectangle
            square_coords = (0, 470, 499, 499)
            draw.rectangle(square_coords, fill=square_color)

        def draw_info(draw, element_info):
            # Define text positions and font sizes
            text_pos1 = (250, 58)
            text_pos2 = (250, 112)
            text_pos3 = (250, 372)
            text_pos4 = (250, 412)

            font1 = ImageFont.truetype(font_path2, size=45)
            font2 = ImageFont.truetype(font_path3, size=220)
            font3 = ImageFont.truetype(font_path2, size=30)
            font4 = ImageFont.truetype(font_path, size=48)

            atomic_number, symbol, atomic_mass, name = (
                element_info[2],
                element_info[1],
                element_info[3],
                element_info[0],
            )

            # Calculate centered positions
            text_width1, _ = textsize(f"{atomic_number}", font=font1)
            text_width2, _ = textsize(symbol, font=font2)
            text_width3, _ = textsize(f"{atomic_mass}", font=font3)
            text_width4, _ = textsize(name, font=font4)

            # Update text positions to center horizontally
            text_pos1 = (250 - text_width1 // 2, text_pos1[1])
            text_pos2 = (250 - text_width2 // 2, text_pos2[1])
            text_pos3 = (250 - text_width3 // 2, text_pos3[1])
            text_pos4 = (250 - text_width4 // 2, text_pos4[1])

            # Draw text on the image using the custom font
            draw.text(text_pos1, f"{atomic_number}", fill=text_color, font=font1)
            draw.text(text_pos2, symbol, fill=text_color, font=font2)
            draw.text(text_pos3, f"{atomic_mass}", fill=text_color, font=font3)
            draw.text(text_pos4, name, fill=text_color, font=font4)

        try:

            image = Image.new("RGB", (width, height), bg_color)

            draw = ImageDraw.Draw(image)
            draw_square(draw)

            element_info = Periodic.get_element(element)
            if element_info:
                draw_info(draw, element_info)
            else:
                print("Element not found")

            output_bytes = BytesIO()
            image.save(output_bytes, format="PNG")

            return output_bytes.getvalue()

        except Exception as e:
            print(f"Error creating image: {e}")
            return None


periodic = Periodic()
