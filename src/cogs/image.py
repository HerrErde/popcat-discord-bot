import random
from io import BytesIO

import disnake
import requests
from disnake.ext import commands
from PIL import Image, ImageEnhance, ImageOps

from helpers import errors
from module.image import (
    apc,
    biden,
    car,
    cmm,
    colorify,
    distort,
    drip,
    fuse,
    gun,
    happysad,
    huerotate,
    opinion,
    pooh,
    ship,
    stonks,
    triggered,
    userquote,
    whowouldwin,
)


class image(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Image")

    @commands.slash_command(name="image")
    async def image(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    # TODO no word wrap
    @image.sub_command(name="cmm", description="Change my Mind Meme")
    async def cmm(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The Text to display."),
    ):
        try:

            output_bytes = cmm.create(text)
            file = disnake.File(BytesIO(output_bytes), filename="cmm.png")

            await inter.response.send_message(file=file)
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @image.sub_command(name="stonks", description="Stonks meme")
    async def stonks(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to use the avatar of"
        ),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            image_bytes = stonks.create(avatar_url)
            file = disnake.File(BytesIO(image_bytes), filename="drip.png")

            await inter.response.send_message(file=file)

        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @image.sub_command(name="triggered", description="Triggered Meme")
    async def triggered(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to use the avatar of"
        ),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

            output_bytes = triggered.create(avatar_url)
            file = disnake.File(BytesIO(output_bytes), filename="triggered.gif")

            await inter.response.send_message(file=file)

        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    # TODO ancor text on one position and only write in one direction
    @image.sub_command(name="opinion", description="Opinion meme")
    async def opinion(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to use the avatar of"
        ),
        text: str = commands.Param(description="The text to display"),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

            image_bytes = opinion.create(text, avatar_url)
            file = disnake.File(BytesIO(image_bytes), filename="quote.png")

            await inter.response.send_message(file=file)
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @image.sub_command(name="whowouldwin", description="Who would win Meme")
    async def whowouldwin(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user1: disnake.User = commands.Param(description="The first user"),
        user2: disnake.User = commands.Param(description="The second user"),
    ):
        try:
            avatar_url_one = (
                user1.avatar.url if user1.avatar else user1.default_avatar.url
            )
            avatar_url_two = (
                user2.avatar.url if user2.avatar else user2.default_avatar.url
            )

            image_bytes = whowouldwin.create(avatar_url_one, avatar_url_two)

            file = disnake.File(BytesIO(image_bytes), filename="whowouldwin.png")

            await inter.response.send_message(file=file)

        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    # TODO cleanup to own file
    # all requests in own file
    @image.sub_command(name="communism", description="Communism Overlay")
    async def communism(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to use the avatar of"
        ),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            overlay_image_path = "../assets/images/communism.png"
            width = 500
            height = 500
            opacity = 0.5

            response_image = requests.get(avatar_url)
            input_image = Image.open(BytesIO(response_image.content))
            input_image = input_image.resize((width, height))
            input_image = input_image.convert("RGBA")

            # Open the predefined overlay image
            overlay = Image.open(overlay_image_path)
            overlay = overlay.resize((width, height))
            overlay = overlay.convert("RGBA")

            # Make the overlay image 50% transparent
            assert 0 <= opacity <= 1, "Opacity must be between 0 and 1."
            alpha = overlay.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
            overlay.putalpha(alpha)

            # Blend the images together using alpha compositing
            blended_image = Image.alpha_composite(input_image, overlay)

            output_bytes = BytesIO()
            blended_image.save(output_bytes, format="PNG")
            output_bytes.seek(0)

            # Send the image back to the interaction
            file = disnake.File(fp=output_bytes, filename="communism.png")
            await inter.send(file=file)

        except Exception as e:
            print(f"Error creating communism image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating communism image: {e}", ephemeral=True
                )
            )

    # TODO cleanup to own file
    # calculate new size on original image size plus new one ?
    @image.sub_command(name="wide", description="Widen an Image")
    async def wide(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to use the avatar of"
        ),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

            response_image = requests.get(avatar_url)
            img = Image.open(BytesIO(response_image.content))
            img = img.convert("RGBA")

            # Calculate the new height to maintain the aspect ratio
            original_width, original_height = img.size

            # Resize the image
            resized_img = img.resize((1500, 600))

            output_bytes = BytesIO()
            resized_img.save(output_bytes, format="PNG")
            output_bytes.seek(0)

            file = disnake.File(fp=output_bytes, filename="wide.png")
            await inter.response.send_message(file=file)
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @image.sub_command(name="distort", description="Distord an Image")
    async def distort(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to use the avatar of"
        ),
        level: int = commands.Param(
            description="The Distortion level. 1-10", ge=1, le=10
        ),
    ):
        await inter.response.defer()

        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

            output_bytes = distort.create(avatar_url, level)

            file = disnake.File(fp=output_bytes, filename="distorted.png")
            await inter.followup.send(file=file)
        except Exception as e:
            print(f"Error creating distorted image: {e}")
            await inter.response.send_message("Error creating distorted image.")

    # TODO right position
    @image.sub_command(name="pooh", description="Tuxedo Pooh meme with 2 texts")
    async def pooh(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text1: str = commands.Param(description="The first Text."),
        text2: str = commands.Param(description="The second Text."),
    ):
        try:
            output_bytes = pooh.create(text1, text2)

            file = disnake.File(BytesIO(output_bytes), filename="pooh.png")
            await inter.response.send_message(file=file)
        except Exception as e:
            print(f"Error creating pooh image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating pooh image: {e}", ephemeral=True
                )
            )

    # TODO cleanup to own file
    @image.sub_command(name="invert", description="Invert an Image")
    async def invert(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to use the avatar of"
        ),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            response = requests.get(avatar_url)
            input_image = Image.open(BytesIO(response.content))

            if input_image.mode == "RGBA":
                input_image = input_image.convert("RGB")

            # Invert the image
            inverted_image = ImageOps.invert(input_image)

            # Convert the inverted image to bytes
            output_bytes = BytesIO()
            inverted_image.save(output_bytes, format="PNG")
            output_bytes.seek(0)

            # Send the inverted image back to the user
            file = disnake.File(fp=output_bytes, filename="inverted.png")
            await inter.response.send_message(file=file)
        except Exception as e:
            print(f"Error creating inverted image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating inverted image: {e}", ephemeral=True
                )
            )

    @image.sub_command(name="happysad", description="Happy and sad meme with 2 texts")
    async def happysad(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text1: str = commands.Param(description="The first Text."),
        text2: str = commands.Param(description="The second Text."),
    ):
        try:
            output_bytes = happysad.create(text1, text2)

            file = disnake.File(BytesIO(output_bytes), filename="happysad.png")
            await inter.response.send_message(file=file)

        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message("Error creating image.")

    @image.sub_command(name="fuse", description="Fuse two user avatars")
    async def fuse(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user1: disnake.User = commands.Param(description="The first User"),
        user2: disnake.User = commands.Param(description="The second User"),
    ):
        try:
            user1_avatar = (
                user1.avatar.url if user1.avatar else user1.default_avatar.url
            )
            user2_avatar = (
                user2.avatar.url if user2.avatar else user2.default_avatar.url
            )
            output_bytes = fuse.create(user1_avatar, user2_avatar)
            file = disnake.File(BytesIO(output_bytes), filename="fused.png")

            await inter.response.send_message(file=file)

        except Exception as e:
            print(f"Error creating happysad image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating happysad image: {e}", ephemeral=True
                )
            )

    # FIXME fix image picker
    @commands.slash_command(name="hue-rotate", description="Rotate the hue of an Image")
    async def huerotate(
        self,
        inter: disnake.ApplicationCommandInteraction,
        degrees: int = commands.Param(
            description="The amount of degree to rotate the hue! [0-360]", ge=0, le=360
        ),
        avatar: disnake.User = commands.Param(
            None, description="The avatar to rotate the hue of"
        ),
        image: disnake.Attachment = commands.Param(
            None, description="Rotate the hue of an image!"
        ),
    ):
        try:
            if not avatar and not image:
                await inter.send("Please choose at least one option! [avatar / image]")
                return

            if avatar:
                image_url = (
                    avatar.avatar.url if avatar.avatar else avatar.default_avatar.url
                )
            else:
                image_url = image.url

            output_bytes = huerotate.create(image_url, degrees)

            if output_bytes:
                file = disnake.File(fp=output_bytes, filename="hue_rotate.png")
                await inter.response.send_message(file=file)
            else:
                await inter.response.send_message(
                    "Failed to process the image.", ephemeral=True
                )
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @commands.slash_command(name="cat", description="See cute Cat Pictures!")
    async def cat(self, inter: disnake.ApplicationCommandInteraction):
        try:
            urls = [
                "https://api.thecatapi.com/v1/images/search?limit=1",
                "https://cataas.com/cat",
            ]

            url = random.choice(urls)

            headers = {"Accept": "application/json"}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            if "application/json" in response.headers.get("content-type"):
                data = response.json()
                if url == "https://api.thecatapi.com/v1/images/search?limit=1":
                    image_url = data[0].get("url")
                else:
                    image_url = "https://cataas.com/cat"
                image_response = requests.get(image_url)
                image_bytes = image_response.content
            else:
                image_bytes = response.content

            embed = disnake.Embed(
                title="",
                color=disnake.Color.random(),
            )
            embed.set_image(url="attachment://cat.png")

            file = disnake.File(BytesIO(image_bytes), filename="cat.png")

            await inter.send(file=file, embed=embed)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching image: {e}")
            await inter.response.send_message("Error fetching image.")
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @commands.slash_command(
        name="car", description="Sends a random Car image with its name."
    )
    async def car(self, inter):
        try:
            image_bytes, title = car.get()

            file = disnake.File(BytesIO(image_bytes), filename="car.png")

            embed = disnake.Embed(
                title=title,
                color=disnake.Color.random(),
            )
            embed.set_image(url="attachment://car.png")

            await inter.response.send_message(embed=embed, file=file)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching image: {e}")
            await inter.response.send_message("Error fetching image.")
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @commands.slash_command(
        name="ship",
        description="Find out how much 2people love each other",
    )
    async def ship(
        self,
        inter: disnake.ApplicationCommandInteraction,
        one: disnake.User = commands.Param(description="The first user"),
        two: disnake.User = commands.Param(description="The second user"),
    ):
        try:
            avatar_url_one = one.avatar.url if one.avatar else one.default_avatar.url
            avatar_url_two = two.avatar.url if two.avatar else two.default_avatar.url

            # Calculate love percentage (for demonstration, a random percentage)
            love_percentage = random.randint(1, 100)

            # Calculate number of filled squares based on percentage
            filled_squares = love_percentage // 10
            empty_squares = 10 - filled_squares

            # Build the response string with filled and empty squares
            response = f"{''.join(':red_square:' for _ in range(filled_squares))}{''.join(':black_large_square:' for _ in range(empty_squares))} {love_percentage}%"

            image_bytes = ship.create(avatar_url_one, avatar_url_two)

            file = disnake.File(BytesIO(image_bytes), filename="ship.png")

            # Build the embed message
            embed = disnake.Embed(
                title="Shipping...",
                description=f"Shipped **{one.display_name}#{one.discriminator}** and **{two.display_name}#{two.discriminator}**!",
                colour=disnake.Color.red(),
            )
            embed.add_field(name=f"**Ship Meter**:", value=response, inline=False)
            embed.set_image(url="attachment://ship.png")  # Set image in embed

            await inter.response.send_message(embed=embed, file=file)

        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @commands.slash_command(
        name="business-card",
        description="Replicate Patrick Bateman's business card from American Psycho with your own information.",
    )
    async def businesscard(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str = commands.Param(description="Name to be displayed"),
        title: str = commands.Param(default="Vice President", description="Your title"),
        company: str = commands.Param(
            default="Pierce & Pierce", description="Company name"
        ),
        tagline: str = commands.Param(
            default="Mergers and Aquisitions", description="Company tagline"
        ),
    ):
        try:
            image_bytes = apc.create(
                name,
                title,
                company,
                tagline,
            )
            file = disnake.File(BytesIO(image_bytes), filename="buissnes-card.png")

            await inter.response.send_message(file=file)

        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @commands.slash_command(
        name="gun",
        description="Add a gun overlay on someone's avatar",
    )
    async def gun(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(description="User"),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

            image_bytes = gun.create(avatar_url)
            file = disnake.File(BytesIO(image_bytes), filename="gun.png")

            embed = disnake.Embed(
                title="",
                description="",
                colour=0xE67E22,
            )
            embed.set_image(url="attachment://gun.png")

            await inter.response.send_message(embed=embed, file=file)

        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @image.sub_command(
        name="drip",
        description="Add a gun overlay on someone's avatar",
    )
    async def drip(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(description="User"),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            image_bytes = drip.create(avatar_url)

            file = disnake.File(BytesIO(image_bytes), filename="drip.png")
            await inter.response.send_message(file=file)

        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @commands.slash_command(
        name="biden",
        description="Make a Biden Tweet with your text!",
    )
    async def biden(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="Text to be displayed on the image"),
    ):
        try:
            image_bytes = biden.create(text)

            file = disnake.File(BytesIO(image_bytes), filename="biden.png")
            await inter.response.send_message(file=file)
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @commands.slash_command(
        name="quote",
        description="Quote any text from a particular user!",
    )
    async def quote(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(description="The User"),
        text: str = commands.Param(description="Text to quote"),
    ):
        try:

            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            username = user.display_name

            image_bytes = userquote.create(text, avatar_url, username)

            file = disnake.File(BytesIO(image_bytes), filename="quote.png")
            await inter.response.send_message(file=file)
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )

    @commands.slash_command(
        name="colorify", description="Overlay any Color on a User's avatar"
    )
    async def colorify(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User whose avatar you want to colorify"
        ),
        color: str = commands.Param(
            description="Common color names such as blue, gold, cyan, or a hex color code."
        ),
    ):
        try:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

            image_bytes = colorify.create(avatar_url, color)

            file = disnake.File(BytesIO(image_bytes), filename="colorify.png")
            await inter.response.send_message(file=file)
        except Exception as e:
            print(f"Error creating image: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error creating image: {e}", ephemeral=True
                )
            )


def setup(bot):
    bot.add_cog(image(bot))
