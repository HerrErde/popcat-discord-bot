import json
import random
import traceback
from io import BytesIO
from math import atan2, cos, radians, sin, sqrt

import disnake
import requests
from disnake.ext import commands
from PIL import Image

from db import DBHandler, RedisHandler
from helpers import errors


# Function to fetch country data
def fetch_country_data():
    try:
        url = "https://countryinfoapi.com/api/countries"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError, KeyError):
        return None
    except Exception as e:
        print(f"Error fetching country list: {e}")
        print(traceback.format_exc())


def fetch_country_shortcode(country):
    try:
        url = f"https://countryinfoapi.com/api/countries/name/{country}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()  # Parse JSON response
        return data.get("cca2", "").lower()
    except (requests.RequestException, ValueError, KeyError):
        return None
    except Exception as e:
        print(f"Error fetching country info: {e}")
        print(traceback.format_exc())


# Fetch country data once and store it
country_data = fetch_country_data()


# Function to calculate distance between two coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


# Function to fetch country names
def fetch_country_names():
    country_names = [country.get("name", "") for country in country_data]
    return sorted(country_names)


# Fetch country names once and store them
country_names = fetch_country_names()


class game(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()
        self.redis_client = None

    async def init_redis(self):
        self.redis_client = await RedisHandler().get_client()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Game")
        await self.db_handler.initialize()

    @commands.slash_command(name="guess-the-country")
    async def guessthecountry(
        self, inter: disnake.ApplicationCommandInteraction, *args
    ):
        pass

    @staticmethod
    async def fetch_country_image(shortcode):
        try:
            image_url = f"https://raw.githubusercontent.com/djaiss/mapsicon/master/all/{shortcode}/1024.png"

            # Fetch and process the image
            response = requests.get(image_url)
            response.raise_for_status()

            output_bytes = BytesIO(response.content)
            image_data = Image.open(output_bytes).convert(
                "RGBA"
            )  # Convert to RGBA to preserve transparency

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

            # Convert the processed image back to bytes
            output_bytes = BytesIO()
            inverted_img.save(output_bytes, format="PNG")
            output_bytes.seek(0)

            return output_bytes
        except Exception as e:
            print(f"Error fetching country image: {e}")

    # TODO setting to see the country image in white or black
    @guessthecountry.sub_command(name="start", description="Start the Game!")
    async def start(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):

        await inter.response.defer()
        user_id = str(inter.author.id)

        try:
            await game.init_redis(self)
            session_data = await self.redis_client.hgetall(f"{user_id}:game")

            # Check if the user already has an active session
            if session_data:
                await inter.followup.send(
                    "You have already started a game! Use /guess-the-country giveup to stop it."
                )
                return

            # Get random country data
            random_country = random.choice(country_data)

            # TODO change it to only saving cca2 code and fetching everything along the way
            # Get random country shortcode, name, and latlng
            shortcode = random_country.get("cca2", "").lower()
            country_name = random_country.get("name", "")
            country_latlng = random_country.get("latlng", [0, 0])

            if not country_latlng or len(country_latlng) != 2:
                await inter.followup.send(
                    "Error: Invalid country data. Please try again."
                )
                return

            output_bytes = await self.fetch_country_image(shortcode)

            embed = disnake.Embed(
                title="Game Started!",
                description=f"Make your first guess by using /guess <country>",
                color=disnake.Color.green(),
            )

            # Set the processed image as the main image in the embed
            file = disnake.File(output_bytes, filename="country.png")
            embed.set_image(url="attachment://country.png")

            # Set session data for the user
            # Save session data to Redis
            await self.redis_client.hmset(
                f"{user_id}:game",
                {
                    "country_name": country_name,
                    "latlng": json.dumps(country_latlng),
                    "shortcode": shortcode,
                },
            )
            await inter.followup.send(embed=embed, file=file)

            # If the user ID is in config.OWNER_USER_IDS, send an ephemeral message with the country name
            """
            if inter.author.id in config.OWNER_USER_IDS:
                await inter.followup.send(
                    f"The country is: {country_name}", ephemeral=True
                )
            """

        except requests.exceptions.RequestException as e:
            print(f"Error fetching random country data: {e}")
            await inter.followup.send("Error fetching random country data.")
        except Image.UnidentifiedImageError:
            # Handle the case where the image cannot be identified
            print(f"Error: Cannot identify image file of country : {country_name}.")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Error starting game: {e}", ephemeral=True
                )
            )
        except Exception as e:
            print(f"Error starting game: {e}")
            print(traceback.format_exc())
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Error starting game: {e}", ephemeral=True
                )
            )

    # DEBUG COMMAND
    @commands.is_owner()
    @guessthecountry.sub_command(
        name="session", description="Show all active game sessions!"
    )
    async def session(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        """
        Displays all active game sessions.
        """
        try:
            await game.init_redis(self)

            # Fetch all keys matching the pattern
            session_keys = await self.redis_client.keys("*:game")

            if not session_keys:
                await inter.response.send_message(
                    "No active game sessions.", ephemeral=True
                )
                return

            embed = disnake.Embed(
                title="Active Game Sessions", color=disnake.Color.blue()
            )

            for key in session_keys:
                user_id = int(key.decode("utf-8").replace(":game", ""))
                user = await self.bot.fetch_user(user_id)

                session_data = await self.redis_client.hgetall(key)

                target_country_name = session_data.get(
                    b"country_name", b"Unknown"
                ).decode("utf-8")
                target_latlng = session_data.get(b"latlng", b"0,0").decode("utf-8")
                history = session_data.get(b"history", b"1").decode("utf-8")

                embed.add_field(
                    name=f"Session `{key.decode('utf-8')}` | Player: {user.name}",
                    value=(
                        f"**Target Country:** {target_country_name}\n"
                        f"**Latitude/Longitude:** {target_latlng}\n"
                        f"**Guesses:** {history}\n"
                    ),
                    inline=False,
                )

            await inter.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error getting game sessions: {e}")
            if not inter.response.is_done():
                await inter.response.send_message(
                    embed=errors.create_error_embed(
                        f"Error getting game sessions: {e}"
                    ),
                    ephemeral=True,
                )
            else:
                await inter.followup.send(
                    embed=errors.create_error_embed(
                        f"Error getting game sessions: {e}"
                    ),
                    ephemeral=True,
                )

    @commands.is_owner()
    @guessthecountry.sub_command(name="cheat", description="Cheat at the Game!")
    async def cheat(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="View the users current game's answer.", default=None
        ),
    ):

        await inter.response.defer()

        if user is None:
            user = inter.author

        user_id = str(user.id)

        try:
            await game.init_redis(self)
            session_data = await self.redis_client.hgetall(f"{user_id}:game")

            # Check if the user already has an active session
            if not session_data:
                if user_id == inter.author.id:
                    await inter.followup.send(
                        "You have not started a game! Use /guess-the-country start to beginn."
                    )
                else:
                    await inter.followup.send("The user has not started a game!")
                return

            if session_data:
                country_name = session_data.get(b"country_name", b"").decode("utf-8")

                await inter.followup.send(
                    f"The country is: `{country_name}`", ephemeral=True
                )

        except requests.exceptions.RequestException as e:
            print(f"Error fetching country data: {e}")
            await inter.followup.send("Error fetching country data.")

        except Exception as e:
            print(f"Error cheating game: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Error cheating game: {e}", ephemeral=True
                )
            )

    async def autocomp_country(
        inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        # Filter and limit the list to 25 items
        filtered_countries = [
            country
            for country in country_names
            if user_input.lower() in country.lower()
        ]
        return filtered_countries[:25]

    @guessthecountry.sub_command(name="guess", description="Guess a Country!")
    async def guess(
        self,
        inter: disnake.ApplicationCommandInteraction,
        country: str = commands.Param(autocomplete=autocomp_country),
    ):
        await inter.response.defer()
        user_id = str(inter.author.id)

        try:
            await game.init_redis(self)
            session_data = await self.redis_client.hgetall(f"{user_id}:game")

            if not session_data:
                await inter.followup.send(
                    "You haven't started a game! Use `/guess-the-country start` to start a new game."
                )
                return

            # Decode and parse the session data
            target_country_name = session_data.get(b"country_name", b"").decode("utf-8")
            shortcode = session_data.get(b"shortcode", b"").decode("utf-8")
            history = int(
                session_data.get(b"history", b"1").decode("utf-8")
            )  # Convert to int and default to 1

            # Handle latlng (it might be a string or already a list)
            latlng = session_data.get("latlng", "[0, 0]")
            if isinstance(latlng, str):
                target_latlng = json.loads(latlng)  # Parse JSON string
            elif isinstance(latlng, list):
                target_latlng = latlng  # Use directly if it's already a list
            else:
                target_latlng = [0, 0]  # Default to [0, 0] if invalid

            # Look up the guessed country in country_data
            guessed_country_data = next(
                (
                    c
                    for c in country_data
                    if c.get("name", "").lower() == country.lower()
                ),
                None,
            )

            if not guessed_country_data:
                await inter.followup.send("Invalid country name.")
                return

            # Get the guessed country's latlng
            guessed_latlng = guessed_country_data.get("latlng", [0, 0])
            if not guessed_latlng or len(guessed_latlng) != 2:
                await inter.followup.send("Error: Invalid guessed country data.")
                return

            # Calculate the distance between the guessed country and the target country
            distance = calculate_distance(
                target_latlng[0],
                target_latlng[1],
                guessed_latlng[0],
                guessed_latlng[1],
            )

            # Fetch the country image
            output_bytes = await self.fetch_country_image(shortcode)
            if not output_bytes:
                await inter.followup.send("Error: Could not fetch country image.")
                return

            # Prepare the embed and file
            file = disnake.File(output_bytes, filename="country.png")
            embed = disnake.Embed()

            if country.lower() == target_country_name.lower():
                # Correct guess
                embed.title = "GG"
                embed.description = (
                    "<a:tada:1269568942377140244> You guessed the correct country!"
                )
                embed.color = disnake.Color.green()
                embed.add_field(name="Guesses", value=f"`{history}`", inline=True)
                embed.set_footer(text="Congratulations!")
                embed.set_image(url="attachment://country.png")

                # Save the result to the database
                await self.db_handler.set_guessthecountry(user_id, country, history)

                # Delete the session data
                await self.redis_client.delete(f"{user_id}:game")
            else:
                # Incorrect guess
                history += 1
                embed.title = "Wrong!"
                embed.color = disnake.Color.red()
                embed.add_field(name="Your Guess", value=f"`{country}`", inline=True)
                embed.add_field(
                    name="Distance From Target",
                    value=f"`{distance:.3f} KM`",
                    inline=True,
                )
                embed.set_image(url="attachment://country.png")

                # Update the session data with the new history value
                await self.redis_client.hset(f"{user_id}:game", "history", str(history))

            # Send the response
            await inter.followup.send(embed=embed, file=file)

        except Exception as e:
            print(f"Error handling guess: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error handling guess: {e}")
            )

    @guessthecountry.sub_command(
        name="giveup", description="Give up on the Country game."
    )
    async def giveup(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):

        await inter.response.defer()
        user_id = str(inter.author.id)

        try:
            await game.init_redis(self)
            session_data = await self.redis_client.hgetall(f"{user_id}:game")

            if session_data:
                target_country_name = session_data.get(b"country_name", b"").decode(
                    "utf-8"
                )
                shortcode = session_data.get(b"shortcode", b"").decode("utf-8")
                history = session_data.get("history", b"0").decode("utf-8")

                output_bytes = await self.fetch_country_image(shortcode)

                # Find the guessed country's data
                guessed_country_data = next(
                    (
                        c
                        for c in country_data
                        if c.get("name", "").lower() == target_country_name.lower()
                    ),
                    None,
                )

                if guessed_country_data:
                    embed = disnake.Embed(
                        title="You Gave Up!",
                        description="",
                        color=disnake.Color.red(),
                    )
                    embed.add_field(
                        name="Number of Attempts",
                        value=f"`{history}`",
                        inline=True,
                    )
                    embed.add_field(
                        name="Country",
                        value=f"`{target_country_name}`",
                        inline=True,
                    )
                    # Set the processed image as the main image in the embed
                    file = disnake.File(output_bytes, filename="country.png")
                    embed.set_image(url="attachment://country.png")

                    await inter.followup.send(embed=embed, file=file)
                    await self.redis_client.delete(f"{user_id}:game")
            else:
                await inter.followup.send(
                    "You need to start a game first! Use /guess-the-country start to start a game."
                )

        except Exception as e:
            print(f"Error handling giveup: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Error handling giveup: {e}", ephemeral=True
                )
            )

    async def fetch_history_embeds(self, user, position):
        try:
            user_id = str(user.id)
            history_data = await self.db_handler.history_guessthecountry(user_id)

            if not history_data or not history_data.get("history"):
                return None, 0

            total_items = len(history_data["history"])

            if position < 0 or position >= total_items:
                return None, total_items

            session_data = history_data["history"][position]
            country_name = session_data.get("country", "Unknown")
            timestamp = session_data.get("date", "Unknown")
            attempts = session_data.get("guesses", "Unknown")

            embed = disnake.Embed(
                title=f"**{user.name}{'#' + user.discriminator if user.discriminator != '0' else ''}'s Sessions | Item {position + 1}/{total_items}**",
                color=disnake.Color.green(),
            )
            embed.add_field(name="Date", value=f"<t:{timestamp}:f>", inline=True)
            embed.add_field(name="Country", value=f"`{country_name}`", inline=True)
            embed.add_field(name="Attempts", value=f"`{attempts}`", inline=True)

            shortcode = fetch_country_shortcode(country_name)
            if shortcode:
                embed.set_image(
                    url=f"https://raw.githubusercontent.com/djaiss/mapsicon/master/all/{shortcode}/1024.png"
                )

            return embed, total_items

        except Exception as e:
            print(f"Error creating embed for history: {e}")
            return None, 0

    @guessthecountry.sub_command(
        name="history", description="View a User's Past Sessions"
    )
    async def history(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="View this User's Past Sessions."
        ),
    ):
        await inter.response.defer()
        position = 0
        try:
            embed, total_items = await self.fetch_history_embeds(user, position)
            if not embed:
                await inter.followup.send(
                    f"**{user.display_name}** has no past sessions!"
                )
                return

            async def button_callback(interaction: disnake.MessageInteraction):
                custom_id = interaction.data["custom_id"]
                action, new_position = custom_id.split(":")
                new_position = int(new_position)

                if action == "history_previous":
                    new_position = max(new_position - 1, 0)
                elif action == "history_next":
                    new_position = min(new_position + 1, total_items - 1)

                new_embed, _ = await self.fetch_history_embeds(user, new_position)
                await interaction.response.edit_message(
                    embed=new_embed, view=create_pagination_view(new_position)
                )

            def create_pagination_view(current_position):
                view = disnake.ui.View()
                prev_button = disnake.ui.Button(
                    label="Previous",
                    style=disnake.ButtonStyle.red,
                    custom_id=f"history_previous:{current_position}",
                    disabled=(current_position == 0),
                )
                next_button = disnake.ui.Button(
                    label="Next",
                    style=disnake.ButtonStyle.green,
                    custom_id=f"history_next:{current_position}",
                    disabled=(current_position == total_items - 1),
                )
                prev_button.callback = button_callback
                next_button.callback = button_callback
                view.add_item(prev_button)
                view.add_item(next_button)
                return view

            await inter.followup.send(
                embed=embed, view=create_pagination_view(position), ephemeral=True
            )

        except Exception as e:
            print(f"Error retrieving user history: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Error retrieving user history: {e}", ephemeral=True
                )
            )

    @guessthecountry.sub_command(
        name="leaderboard",
        description="Display the top 10 users with the most games won.",
    )
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

        try:
            # Call DBHandler method to retrieve leaderboard data
            top_games = await self.db_handler.list_guessthecountry()
            # print(f"Top games: {top_games}")  # Debug logging

            if not top_games:
                await inter.followup.send("No data found in the leaderboard.")
                return

            # Initialize a dictionary to map user IDs to usernames
            user_names = {}

            # Fetch user data for each user ID individually
            for user_id in top_games.keys():
                try:
                    user = await inter.bot.fetch_user(int(user_id))
                    user_names[user_id] = (
                        f"{user.name}{'#' + user.discriminator if user.discriminator != '0' else ''}"
                    )
                except Exception as e:
                    print(f"Error fetching user {user_id}: {e}")
                    user_names[user_id] = "Unknown User"

            # Construct the leaderboard description
            leaderboard_description = "Here are the top 10 users with the most games won.\n" + "\n".join(
                f"{i}. **{user_names.get(user_id, 'Unknown User')}** - **{games_won}** games won."
                for i, (user_id, games_won) in enumerate(top_games.items(), 1)
            )

            # Create the embed with the leaderboard description
            embed = disnake.Embed(
                title="Leaderboard",
                description=leaderboard_description,
                color=disnake.Color.green(),
            )

            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Error getting leaderboardy: {e}", ephemeral=True
                )
            )


def setup(bot):
    bot.add_cog(game(bot))
