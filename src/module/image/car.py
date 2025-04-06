import random
from io import BytesIO

import asyncpraw
import requests
from PIL import Image

import config

carporn_url = "https://www.reddit.com/r/carporn.json"
car_url = "https://www.reddit.com/r/cars.json"


def get():
    try:
        while True:
            url = random.choice([carporn_url, car_url])

            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
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


async def reddit():
    try:
        while True:
            reddit = asyncpraw.Reddit(
                client_id=config.REDDIT_ID,
                client_secret=config.REDDIT_SECRET,
                user_agent="discord:popcat:v1.0 (by /u/herrerde)",
            )
            subreddit_name = random.choice(["carporn", "car"])
            subreddit = await reddit.subreddit(subreddit_name)

            # Fetch top posts from the subreddit
            posts = await subreddit.top(limit=50)

            if subreddit_name == "car":
                filtered_posts = [
                    post async for post in posts if post.link_flair_text == "picture"
                ]
                if not filtered_posts:
                    continue  # Retry if no posts with the right flair text found
                random_post = random.choice(filtered_posts)
            else:
                random_post = random.choice([post async for post in posts])

            title = random_post.title
            url_post = random_post.url

            async with reddit.session.get(url_post) as response:
                response.raise_for_status()
                try:
                    image = Image.open(BytesIO(await response.read()))

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

    except Exception as e:
        print(f"Error occurred during retrieval: {str(e)}")
        return None
