import asyncio
import random
from datetime import datetime

import config
import disnake
import requests
from bs4 import BeautifulSoup
from disnake.ext import commands

from helpers import errors


class misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Misc")

    @commands.slash_command(name="enlarge", description="Enlarge an Emoji!")
    async def enlarge(
        self,
        inter: disnake.ApplicationCommandInteraction,
        emoji: str = commands.Param(description="The emoji to enlarge"),
    ):
        try:
            # Check if the emoji is a custom emoji
            if emoji.startswith("<") and emoji.endswith(">"):
                # Extract custom emoji details
                animated = emoji.startswith("<:a:")
                emoji_id = emoji.split(":")[-1][:-1]
                emoji_name = emoji.split(":")[1]
                emoji_ext = "gif" if animated else "png"
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{emoji_ext}"

                embed = disnake.Embed(title=emoji_name, color=disnake.Color.blurple())
                embed.set_footer(text=f"ID - {emoji_id}")

                embed.set_image(url=emoji_url)

            else:
                # Split emoji into individual characters and get the URL for each
                emoji_urls = []
                for char in emoji:
                    unicode_code_points = f"{ord(char):x}"
                    # emoji_url = f"https://raw.githubusercontent.com/jdecked/twemoji/refs/heads/main/assets/72x72/{unicode_code_points}.png"
                    # emoji_url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/15.1.0/72x72/{unicode_code_points}.png"
                    emoji_url = f"https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/{unicode_code_points}.png"
                    emoji_urls.append(emoji_url)

                # Create an embed
                embed = disnake.Embed(title="", color=disnake.Color.blurple())

                # If more than one emoji, add links
                if len(emoji_urls) > 1:
                    for emoji_url in emoji_urls:
                        embed.add_field(
                            name="Emoji",
                            value=f"[Click here]({emoji_url})",
                            inline=True,
                        )
                else:
                    # If only one emoji, add it as an image directly
                    embed.set_image(url=emoji_urls[0])

                await inter.send(embed=embed)

        except Exception as e:
            print(f"Error enlarging emoji: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error sending serverinfo command: {e}"
                )
            )

    @commands.slash_command(name="qrcode", description="Create a QR Code for a URL.")
    async def qrcode(
        self,
        inter: disnake.ApplicationCommandInteraction,
        url: str = commands.Param(description="The URL to create a QR Code for"),
    ):
        try:

            qr_code_url = (
                f"http://api.qrserver.com/v1/create-qr-code/?data={url}&size=200x200"
            )

            embed = disnake.Embed(
                title="Successfully Generated QR Code!", color=disnake.Color.green()
            )
            # Set the QR code image in the embed
            embed.set_image(url=qr_code_url)

            await inter.send(embed=embed)

        except Exception as e:
            print(f"Error creating QR Code: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error creating QR Code: {e}")
            )

    @commands.slash_command(name="embed", description="Create a custom embed.")
    async def emebd(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(description="Embed Title"),
        description: str = commands.Param(description="Embed description"),
        color: str = commands.Param(description="Embed Color"),
        footer: str = commands.Param(description="Embed Footer"),
    ):
        await inter.response.defer()
        try:
            # Convert hexadecimal color string to integer
            color_int = int(color.lstrip("#"), 16)

            embed = disnake.Embed(title=title, description=description, color=color_int)

            # Set the footer
            embed.set_footer(text=footer)

            await inter.followup.send("Embed send!")
            await inter.send(embed=embed)

        except Exception as e:
            print(f"Error creating embed: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error creating embed: {e}")
            )

    @commands.slash_command(
        name="today", description="See what happend on this day in History."
    )
    async def today(self, inter: disnake.ApplicationCommandInteraction):
        try:
            # Get the current date
            current_date = datetime.now()
            current_month = current_date.strftime("%B")
            current_day = int(current_date.strftime("%d"))

            url = f"https://en.wikipedia.org/wiki/{current_month}_{current_day}"

            response = requests.get(url)

            soup = BeautifulSoup(response.content, "html.parser")

            def extract_events(soup):
                events = []
                events_heading = soup.find(id="Events")
                if events_heading:
                    events_list = events_heading.find_next("ul")
                    if events_list:
                        for event in events_list.find_all("li"):
                            for sup in event.find_all("sup"):
                                sup.extract()
                            events.append(event.text.strip())
                return events

            # Get all historical events for the current month and day
            events = extract_events(soup)

            random_event = random.choice(events)

            title = f"On {current_month} {current_day}..."
            if random_event:
                event = random_event
            else:
                event = "Where no historical events found."

            embed = disnake.Embed(
                title=title, description=event, color=disnake.Color.orange()
            )

            await inter.send(embed=embed)

        except Exception as e:
            print(f"Error getting Todays Text: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error getting Todays Text: {e}")
            )

    @commands.slash_command(
        name="google-autocomplete",
        description="Responds with a list of the Google Autofill results for a particular query.",
    )
    async def autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        query: str = commands.Param(description="The Google Search query"),
    ):
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=chrome&q={query}"

            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            # Get the first ten autocomplete suggestions
            results = data[1][:10]
            # Construct a readable response
            autocomplete_suggestions = "\n".join(results)
            response_content = f"**Query:** {query}\n{autocomplete_suggestions}"
            # Send the response to the user
            await inter.response.send_message(content=response_content)

        except Exception as e:
            print(f"Error getting google autocomplete: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error getting google autocomplete: {e}"
                )
            )

    @commands.slash_command(
        name="choose",
        description="Choose between multiple Options.",
    )
    async def choose(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option_1: str = commands.Param(description="The first option."),
        option_2: str = commands.Param(description="The second option."),
        option_3: str = commands.Param(default=None, description="The third option."),
        option_4: str = commands.Param(default=None, description="The forth option."),
        option_5: str = commands.Param(default=None, description="The fith option."),
        option_6: str = commands.Param(default=None, description="The sixth option."),
        option_7: str = commands.Param(default=None, description="The seventh option."),
        option_8: str = commands.Param(default=None, description="The eight option."),
    ):
        try:
            # Collect all provided options into a list
            options = [
                option_1,
                option_2,
                option_3,
                option_4,
                option_5,
                option_6,
                option_7,
                option_8,
            ]
            # Remove any None values from the list (optional)
            options = [option for option in options if option is not None]

            if len(options) < 2:
                await inter.response.send_message(
                    content="Please provide at least two options."
                )
                return

            # Randomly choose an option index
            chosen_option_index = random.randint(0, len(options) - 1)
            chosen_option = options[chosen_option_index]

            embed = disnake.Embed(
                title="",
                description=f"I choose {chosen_option}.",
                color="#eb459e",
            )

            await inter.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error creating choose message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error creating choose message: {e}")
            )

    @commands.slash_command(
        name="poll",
        description="Create a Poll!",
    )
    async def poll(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(description="Poll Title"),
        one: str = commands.Param(description="Option one"),
        two: str = commands.Param(description="Option two"),
    ):
        try:

            embed = disnake.Embed(
                title=title,
                description=f":one: {one}\n\n:two: {two}",
                color=disnake.Color.blurple(),
            )
            embed.set_footer(
                text=f"Poll created by {inter.author.name}",
                icon_url=inter.author.avatar.url if inter.author.avatar else None,
            )

            await inter.response.send_message(embed=embed)
            message = await inter.original_message()

            # Add reactions to the message
            await message.add_reaction("1️⃣")
            await message.add_reaction("2️⃣")
        except Exception as e:
            print(f"Error creating poll: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error creating poll: {e}")
            )

    dino_art = [
        "**---------------:t_rex:**",
        "**-----------:t_rex:----**",
        "**----------:t_rex:------**",
        "**--------:t_rex:--------**",
        "**------:t_rex:-----------**",
        "**-------:t_rex:-----------**",
        "**---:cactus:-----:t_rex:---------**",
        "**---:cactus:-:t_rex:-------------**",
        "**:t_rex:\n ---:cactus:--------------**",
        "**------:t_rex:---:cactus:--------------**",
        "**----:t_rex:-----:cactus:----------------**",
        "**-:cactus::cactus:-----:t_rex:-------:cactus:--------**",
        "**----:cactus::cactus:-:t_rex:----------:cactus:------**",
        "**:t_rex:\n ---:cactus::cactus:-------------:cactus:---**",
        "**-----:t_rex:---:cactus::cactus:-------------:cactus:--**",
        "**-------:t_rex:-----:cactus::cactus:-------------**",
        "**:birthday:----:t_rex:--------:cactus::cactus:-----------**",
        "**---:birthday:--:t_rex:----------:cactus::cactus:---------**",
        "**Mission Completed! !**\n **---:birthday::t_rex:----------:cactus::cactus:-------------**",
    ]

    @commands.slash_command(name="dino", description="Chrome Dino Game")
    async def dino(self, inter: disnake.ApplicationCommandInteraction):
        # Send the first message
        await inter.response.send_message(misc.dino_art[0])

        # Update the message with the rest of the list
        message = await inter.original_message()
        for art in misc.dino_art[1:]:
            await message.edit(content=art)
            await asyncio.sleep(1)

    @commands.slash_command(
        name="report", description="Report a bug to the bot developer."
    )
    async def report(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The content."),
    ):
        try:
            # Get the report channel from the bot configuration
            report_channel_id = config.REPORT_CHANNEL
            channel = self.bot.get_channel(int(report_channel_id))

            if not channel:
                raise ValueError("Report channel not found")

            # Get current date and time
            now = datetime.utcnow()
            date = now.strftime("%d.%m.%Y")
            time = now.strftime("%H:%M:%S")

            embed = disnake.Embed(
                title="Bug Report!", description=text, color=disnake.Color.green()
            )
            embed.set_author(name=inter.author.name, icon_url=inter.author.avatar.url)
            embed.set_footer(text=f"{date} {time}")

            await channel.send(embed=embed)

            await inter.response.send_message(content="Report Sent!", ephemeral=True)

        except Exception as e:
            print(f"Error sending report message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error sending report: {e}")
            )


def setup(bot):
    bot.add_cog(misc(bot))
