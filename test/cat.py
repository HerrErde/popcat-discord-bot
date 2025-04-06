import random

import requests


def cat():
    urls = [
        "https://api.thecatapi.com/v1/images/search?limit=1",
        "https://cataas.com/cat",
    ]

    url = random.choice(urls)

    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        if "application/json" in response.headers.get("content-type"):
            data = response.json()
            if url == "https://api.thecatapi.com/v1/images/search?limit=1":
                image = data[0].get("url")
            else:
                image = "No cat image available."
        else:
            image = response.content

        return image

    except requests.exceptions.RequestException as e:
        print(f"Error fetching image: {e}")
        return "Error fetching image."
