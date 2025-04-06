from PIL import Image


def profile_avatar():
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

    response_image = requests.get(avatar_url)
    img = Image.open(BytesIO(response_image.content))
    img = img.convert("RGBA")
    return img
