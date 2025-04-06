from io import BytesIO

import pycountry
import requests
from geopy.geocoders import Nominatim
from haversine import haversine
from PIL import Image, ImageDraw, ImageFont

font_path = "akhandsoft_bold.otf"
img_path = "distance.png"


def is_valid_country(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return country.name == country_name
    except LookupError:
        return False


def get_coordinates(country_name):
    geolocator = Nominatim(user_agent="country_distance_calculator")
    location = geolocator.geocode(country_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        return None


def calculate_distance(country1, country2):
    coords1 = get_coordinates(country1)
    coords2 = get_coordinates(country2)

    if not coords1 or not coords2:
        print(f"Could not find coordinates for {' or '.join([country1, country2])}")
        return None

    distance = haversine(coords1, coords2)
    return distance


def fetch_country_icon(country):
    try:
        url = f"https://countryinfoapi.com/api/countries/name/{country}"
        response = requests.get(url)
        response.raise_for_status()
        country_data = response.json()
        shortcode = country_data.get("cca2", "").lower()
        image_url = f"https://raw.githubusercontent.com/djaiss/mapsicon/master/all/{shortcode}/1024.png"
        image_response = requests.get(image_url)
        response.raise_for_status()

        output_bytes = BytesIO(image_response.content)
        image_data = Image.open(output_bytes).convert("RGBA")

        # Invert colors
        inverted_data = []
        for pixel in image_data.getdata():
            r, g, b, a = pixel
            inverted_r = 255 - r
            inverted_g = 255 - g
            inverted_b = 255 - b
            inverted_data.append((inverted_r, inverted_g, inverted_b, a))

        inverted_img = Image.new("RGBA", image_data.size)
        inverted_img.putdata(inverted_data)

        output_bytes = BytesIO()
        inverted_img.save(output_bytes, format="PNG")
        output_bytes.seek(0)

        return output_bytes
    except Exception as e:
        print(f"Error while trying to fetch icon for {country}: {e}")
        await inter.response.send_message(
            "An error occurred while sending the welcome message.",
            ephemeral=True,
        )
        return None


def create(country1, country2, distance):
    font = ImageFont.truetype(font_path, 15)

    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)

    text_x = 155
    text_y = 53

    # Write text on image
    draw.text((text_x, text_y), f"{distance:.2f} KM", font=font, fill="white")

    # Fetch and paste country icons
    icon1 = fetch_country_icon(country1)
    icon2 = fetch_country_icon(country2)
    if icon1 and icon2:
        icon1_img = Image.open(icon1).convert("RGBA")
        icon2_img = Image.open(icon2).convert("RGBA")

        # Resize icons to a specific percentage
        icon_size_percentage = 11  # Change this value as needed
        icon1_img = icon1_img.resize(
            (
                icon1_img.width * icon_size_percentage // 100,
                icon1_img.height * icon_size_percentage // 100,
            )
        )
        icon2_img = icon2_img.resize(
            (
                icon2_img.width * icon_size_percentage // 100,
                icon2_img.height * icon_size_percentage // 100,
            )
        )

        # Calculate icon position
        icon1_x = 20
        icon1_y = 7
        icon2_x = 270
        icon2_y = 10

        # Paste icons onto image
        img.paste(icon1_img, (icon1_x, icon1_y), icon1_img)
        img.paste(icon2_img, (icon2_x, icon2_y), icon2_img)

    # Save the modified image
    img.save("output.png")
    print("Image with text and icons has been saved as output.png")


if __name__ == "__main__":
    country1 = "Germany"
    country2 = "Canada"

    if country1.strip() == "" or country2.strip() == "":
        print("Please enter valid country names.")
    elif not is_valid_country(country1) or not is_valid_country(country2):
        print("Please enter valid full country names.")
    else:
        distance = calculate_distance(country1, country2)
        if distance is not None:
            create(country1, country2, distance)
        else:
            print("Failed to calculate the distance.")
