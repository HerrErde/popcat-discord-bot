from io import BytesIO

import requests
from geopy.geocoders import Nominatim
from haversine import haversine
from PIL import Image, ImageDraw, ImageFont

font_path = "assets/font/akhandsoft_bold.otf"
img_path = "assets/images/distance.png"


def get_coordinates(country_name):
    geolocator = Nominatim(user_agent="country_distance_calculator")
    location = geolocator.geocode(country_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        print(f"Could not find coordinates for {country_name}")
        return None


def calculate_distance(country1, country2):
    coords1 = get_coordinates(country1)
    coords2 = get_coordinates(country2)

    if not coords1 or not coords2:
        return None

    distance = haversine(coords1, coords2)
    return distance


def fetch_country_icon(country):
    """Fetch and invert the colors of a country's icon."""
    url = f"https://countryinfoapi.com/api/countries/name/{country}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        country_data = response.json()
        shortcode = country_data.get("cca2", "").lower()
        image_url = f"https://raw.githubusercontent.com/djaiss/mapsicon/master/all/{shortcode}/1024.png"
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        output_bytes = BytesIO(image_response.content)
        image_data = Image.open(output_bytes).convert("RGBA")

        # Invert colors
        inverted_data = [
            (255 - r, 255 - g, 255 - b, a) for r, g, b, a in image_data.getdata()
        ]

        inverted_img = Image.new("RGBA", image_data.size)
        inverted_img.putdata(inverted_data)

        output_bytes = BytesIO()
        inverted_img.save(output_bytes, format="PNG")
        output_bytes.seek(0)

        return output_bytes
    except requests.RequestException as e:
        print(f"Failed to fetch icon for {country}: {e}")
        return None


def create(country1, country2):
    distance = calculate_distance(country1, country2)
    if distance is None:
        print("Could not calculate the distance.")
        return None

    try:
        font = ImageFont.truetype(font_path, 15)
        img = Image.open(img_path)
    except IOError as e:
        print(f"Failed to load font or image: {e}")
        return None

    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)

    text_x = 155
    text_y = 53

    draw.text((text_x, text_y), f"{distance:.2f} KM", font=font, fill="white")

    icon1 = fetch_country_icon(country1)
    icon2 = fetch_country_icon(country2)
    if icon1 and icon2:
        icon1_img = Image.open(icon1).convert("RGBA")
        icon2_img = Image.open(icon2).convert("RGBA")

        # Resize icons to a specific percentage
        icon_size_percentage = 11
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

        icon1_x, icon1_y = 20, 7
        icon2_x, icon2_y = 270, 10

        img.paste(icon1_img, (icon1_x, icon1_y), icon1_img)
        img.paste(icon2_img, (icon2_x, icon2_y), icon2_img)

    output_bytes = BytesIO()
    img.save(output_bytes, format="PNG")
    return output_bytes.getvalue(), distance
