import random
from io import BytesIO

import requests
from PIL import Image


SUBREDDITS = ["cars", "carporn"]


def get():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"
    }
    try:
        while True:
            subreddit = random.choice(SUBREDDITS)
            response = requests.get(
                f"https://www.reddit.com/r/{subreddit}.json", headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if (
                data
                and "data" in data
                and "children" in data["data"]
                and len(data["data"]["children"]) > 0
            ):
                if url == car_url:
                    filtered_posts = [
                        post
                        for post in data["data"]["children"]
                        if post["data"].get("link_flair_text") == "picture"
                    ]
                    if not filtered_posts:
                        continue
                    random_post = random.choice(filtered_posts)["data"]
                else:
                    random_post = random.choice(data["data"]["children"])["data"]

                title = random_post.get("title")
                url_post = random_post.get("url")

                response = requests.get(url_post)
                response.raise_for_status()

                try:
                    image = Image.open(BytesIO(response.content))

                    output_bytes = BytesIO()
                    image.save(output_bytes, format="PNG")
                    image_data = output_bytes.getvalue()

                    if title and image_data:
                        return image_data, title
                    else:
                        return None
                except Exception as e:
                    print(f"Error occurred while processing the image: {str(e)}")
                    continue

            else:
                print("No posts found in the response.")
                return None

    except Exception as e:
        print(f"Error occurred during retrieval: {str(e)}")
        return None
