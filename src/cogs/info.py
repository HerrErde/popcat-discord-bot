import json
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO

import asyncpraw
import config
import disnake
import pytz
import requests
from disnake.ext import commands

from helpers import errors
from module.image import distance, periodic
from module.text import color


# Function to fetch country data
def fetch_country_data():
    url = "https://countryinfoapi.com/api/countries"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# Fetch country data once and store it
country_data = fetch_country_data()


# Function to fetch country names
def fetch_country_names():
    country_names = [country.get("name", "") for country in country_data]
    return sorted(country_names)


country_names = fetch_country_names()


class info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

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

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Info")

    @commands.slash_command(
        name="worldclock", description="View the time in different countries!"
    )
    async def worldclock(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer()
        try:
            current_time = datetime.now(pytz.utc)

            date_format = "%m/%d/%Y, %I:%M:%S %p"

            time_zones = [
                ("London", "gb", "GMT", 0, False),
                ("New York", "us", "EST", -5, True),
                ("Los Angeles", "us", "PST", -8, True),
                ("Mexico City", "us", "CST", -7, True),
                ("Sydney", "au", "AEST", 11, True),
                ("Perth", "au", "AWST", 8, True),
                ("Korea", "kr", "KST", 9, False),
                ("India", "in", "IST", 5.5, False),
            ]

            embed = disnake.Embed(
                title="World Clock - Timezones",
                color=disnake.Color.blue(),
            )

            for city, flag, tz_name, offset_hours, inline in time_zones:
                city_time = (current_time + timedelta(hours=offset_hours)).strftime(
                    date_format
                )
                if tz_name == "IST":
                    city_time = current_time.strftime(date_format)
                    offset_str = "GMT+5:30"
                else:
                    offset_str = (
                        f"GMT{'+' if offset_hours >= 0 else ''}{offset_hours:+}:00"
                    )

                embed.add_field(
                    name=f":flag_{flag}: {city} ({tz_name})",
                    value=f"{city_time}\n({offset_str})",
                    inline=inline,
                )

            await inter.send(embed=embed)

        except Exception as e:
            print(f"Error sending worldclock message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error sending worldclock command: {e}"
                )
            )

    @commands.slash_command(
        name="country", description="Get information on a country name."
    )
    async def country(
        self,
        inter: disnake.ApplicationCommandInteraction,
        country: str = commands.Param(
            autocomplete=autocomp_country,
            description="The Country to get information on.",
        ),
    ):
        try:
            url = f"https://countryinfoapi.com/api/countries/name/{country}"
            country_file = "assets/data/countries.json"

            def load_data():
                with open(country_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                return data

            def get_data(country_name):
                data = load_data()
                for country in data:
                    if country["country"].lower() == country_name.lower():
                        famous_for = country.get("famous_for", "Unknown")
                        neighbors = country.get("neighbors", "Unknown")
                        return famous_for, neighbors
                return "None"

            famous_for, neighbors = get_data(country)

            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            name = data.get("name", "Unknown")
            capital = data.get("capital", ["Unknown"])[0]
            currency = (
                data.get("currencies", {})
                .get(list(data.get("currencies", {}).keys())[0], {})
                .get("name", "Unknown")
            )
            languages = ", ".join(data.get("languages", {}).values())
            callingcode = data.get("callingcode", "Unknown")
            driving_side = data.get("car", {}).get("side", "Unknown")
            area = "{:,} km²".format(data.get("area", 0))
            continents = ", ".join(data.get("continents", "Unknown"))
            tld = data.get("tld", "Unknown")[0]
            landlocked = "Yes" if data.get("landlocked") else "No"
            borders = ", ".join(sorted(neighbors))
            famous_for = ", ".join(
                [item.capitalize() for item in famous_for.split(", ")]
            )

            # borders = ", ".join(sorted(data.get("borders", [])))
            # if not borders:
            #    borders = "None"

            shortcode = data.get("cca2", "").lower()
            # image_url = f"https://flagcdn.com/h80/{shortcode}.png"
            image_url = f"https://flagpedia.net/data/flags/h80/{shortcode}.png"

            embed = disnake.Embed(title=f"Country Info for {name}", color=0x36393E)
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Capital", value=capital, inline=True)
            embed.add_field(name="Currency", value=currency, inline=True)
            embed.add_field(name="Languages", value=languages, inline=True)
            embed.add_field(name="Phone Code", value=callingcode, inline=True)
            embed.add_field(name="Famous For", value=famous_for, inline=True)
            embed.add_field(name="Driving Direction", value=driving_side, inline=True)
            embed.add_field(name="Area", value=area, inline=True)
            embed.add_field(name="Continent", value=continents, inline=True)
            embed.add_field(name="TLD", value=tld, inline=True)
            embed.add_field(name="Landlocked", value=landlocked, inline=True)
            embed.add_field(name="Neighbours", value=borders, inline=True)

            embed.set_thumbnail(url=image_url)

            await inter.send(embed=embed)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching country data: {e}")
            await inter.response.send_message("Error fetching country data.")
        except Exception as e:
            print(f"Error processing country command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error processing country command: {e}"
                )
            )

    @commands.slash_command(
        name="distance", description="Calculate distance between two countries."
    )
    async def distance(
        self,
        inter: disnake.ApplicationCommandInteraction,
        country1: str = commands.Param(
            autocomplete=autocomp_country,
            description="The first country to calculate distance from.",
        ),
        country2: str = commands.Param(
            autocomplete=autocomp_country,
            description="The second country to calculate distance to.",
        ),
    ):

        await inter.response.defer()
        try:
            output_bytes, calc_distance = distance.create(country1, country2)

            if output_bytes:
                file = disnake.File(BytesIO(output_bytes), filename="distance.png")
                embed = disnake.Embed(
                    title="Distance Calculator",
                    description=f"Distance Between {country1} and {country2} is **``{calc_distance:.2f}``** KM",
                    color=disnake.Color.green(),
                )
                embed.set_image(url="attachment://distance.png")

                await inter.send(file=file, embed=embed)
            else:
                await inter.send("Failed to create the distance image.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching distance data: {e}")
            await inter.response.send_message("Error fetching distance data.")
        except Exception as e:
            print(f"Error processing distance command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error processing distance command: {e}"
                )
            )

    @commands.slash_command(name="npm", description="Search for npm packages")
    async def npm(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str = commands.Param(
            description="The package name.",
        ),
    ):
        try:
            npm_search = f"https://registry.npmjs.com/-/v1/search?text={name}&size=1"
            npm_api = f"https://api.npmjs.org/downloads/point/last-year/{name}"

            response_search = requests.get(npm_search)
            response_search.raise_for_status()
            response_api = requests.get(npm_api)
            response_api.raise_for_status()

            data_search = response_search.json()
            data_api = response_api.json()

            downloads_this_year = data_api.get("downloads", "None")

            objects = data_search.get("objects", [])
            if objects:
                result = objects[0]["package"]

                name = result.get("name", None)
                version = result.get("version", None)
                description = result.get("description", None)
                keywords = result.get("keywords", [])
                publisher = result.get("publisher", {})
                publisher_username = publisher.get("username", None)
                publisher_email = publisher.get("email", None)
                date = result.get("date", None)
                repository = result.get("links", {}).get("repository", "None")

                keywords_str = ", ".join(keywords) if keywords else "None"

                # Convert the ISO 8601 date string to a datetime object
                date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")

                # Convert the datetime object to a human-readable string
                human_readable_date = date_obj.strftime("%a %b %d %Y")

                embed = disnake.Embed(
                    title=name,
                    description=description,
                    color=0xFFCC99,
                    url=f"https://www.npmjs.com/package/{name}",
                )
                embed.add_field(
                    name="Author",
                    value=publisher_username or "Unknown",
                    inline=True,
                )
                embed.add_field(
                    name="Email", value=publisher_email or "Unknown", inline=True
                )
                embed.add_field(
                    name="Downloads This Year",
                    value=f"{downloads_this_year:,}",
                    inline=True,
                )
                embed.add_field(
                    name="Last Published", value=human_readable_date, inline=True
                )
                embed.add_field(name="Version", value=version, inline=True)
                embed.add_field(
                    name="Repository", value=repository or "None", inline=True
                )
                embed.add_field(
                    name="Maintainers", value=publisher_username, inline=True
                )
                embed.add_field(name="Keywords", value=keywords_str, inline=True)

                embed.set_footer(text=f"Today at {datetime.now().strftime('%H:%M')}")

                await inter.send(embed=embed)
            else:
                await inter.send("No results found for the given package name.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching NPM data: {e}")
            await inter.response.send_message("Error fetching NPM data.")
        except Exception as e:
            print(f"Error processing NPM command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error processing NPM command: {e}")
            )

    @commands.slash_command(
        name="github", description="Get information on a GitHub user!"
    )
    async def github(
        self,
        inter: disnake.ApplicationCommandInteraction,
        username: str = commands.Param(
            description="The username to search for",
        ),
    ):
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
            else:
                await inter.send("User not found.")
                return

            formatted_data = {
                "url": data["html_url"],
                "avatar": data["avatar_url"],
                "name": data["login"],
                "email": data["email"] if data["email"] else "None",
                "bio": data["bio"] if data["bio"] else "No Bio",
                "public_repos": data["public_repos"],
                "followers": data["followers"],
                "following": data["following"],
                "created_at": data["created_at"],
            }
            date_obj = datetime.strptime(
                formatted_data["created_at"], "%Y-%m-%dT%H:%M:%SZ"
            )

            # Convert the datetime object to a human-readable string
            human_readable_date = date_obj.strftime("%a, %b %d %Y %H:%M:%S GMT")

            embed = disnake.Embed(
                title=f"GitHub User Info For {formatted_data['name']}",
                url=formatted_data["url"],
                color=0xFFCC99,
            )
            embed.set_thumbnail(url=formatted_data["avatar"])
            embed.add_field(name="Username", value=formatted_data["name"], inline=True)
            embed.add_field(
                name="Followers", value=formatted_data["followers"], inline=True
            )
            embed.add_field(
                name="Following", value=formatted_data["following"], inline=True
            )
            embed.add_field(
                name="Public Repositories",
                value=formatted_data["public_repos"],
                inline=True,
            )
            embed.add_field(name="Email", value=formatted_data["email"], inline=True)
            embed.add_field(
                name="Account Created At", value=human_readable_date, inline=True
            )
            embed.add_field(name="Bio:", value=formatted_data["bio"], inline=True)

            await inter.send(embed=embed)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub data: {e}")
            await inter.response.send_message("Error fetching GitHub data.")
        except Exception as e:
            print(f"Error processing GitHub command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error processing GitHub command: {e}")
            )

    @commands.slash_command(name="reddit", description="Search for subreddit")
    async def reddit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str = commands.Param(description="Subreddit name."),
    ):
        try:
            reddit = asyncpraw.Reddit(
                client_id=config.REDDIT_ID,
                client_secret=config.REDDIT_SECRET,
                user_agent="discord:popcat:v1.0 (by /u/herrerde)",
            )

            subreddit = await reddit.subreddit(name)

            await subreddit.load()

            title = subreddit.title
            subscribers = subreddit.subscribers
            active_users = subreddit.accounts_active
            created_utc = datetime.fromtimestamp(subreddit.created_utc, timezone.utc)
            created = created_utc.strftime("%a, %b %d %Y")
            description = subreddit.public_description
            over18 = "Yes" if subreddit.over18 else "No"
            icon = subreddit.icon_img or ""
            subreddit_url = f"https://www.reddit.com/r/{subreddit.display_name}/"

            embed = disnake.Embed(
                title=f"r/{subreddit.display_name}",
                url=subreddit_url,
                color=0xFF4500,
            )
            embed.add_field(name="Title", value=title, inline=True)
            embed.add_field(name="Subscribers", value=subscribers, inline=True)
            embed.add_field(name="Active Users", value=active_users, inline=True)
            embed.add_field(name="Over 18", value=over18, inline=True)
            embed.add_field(name="Created", value=created, inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            embed.set_thumbnail(url=icon)

            await inter.send(embed=embed)

        except asyncpraw.exceptions.PRAWException as e:
            print(f"Error fetching Reddit data: {e}")
            await inter.response.send_message("Error fetching Reddit data.")
        except Exception as e:
            print(f"Error processing Reddit command: {e}")
            await inter.response.send_message(f"Error processing Reddit command: {e}")
        finally:
            await reddit.close()

    # TODO add autocomplete witb element name, atomic number, symbol
    @commands.slash_command(
        name="periodic-table",
        description="Find an element on the periodic table.",
    )
    async def periodictable(
        self,
        inter: disnake.ApplicationCommandInteraction,
        element: str = commands.Param(
            description="The element to find. You can enter name, symbol or atomic number."
        ),
    ):
        try:
            element_info = periodic.Periodic.get_element(element)

            if element_info:
                (
                    name,
                    symbol,
                    atomicnumber,
                    atomicmass,
                    period,
                    phase,
                    discovered,
                    summary,
                ) = element_info

                output_bytes = Periodic.create(element)
                file = disnake.File(BytesIO(output_bytes), filename="element.png")

                embed = disnake.Embed(
                    title=name,
                    description="",
                    colour=disnake.Color.yellow(),
                )
                embed.add_field(name="Symbol", value=f"`{symbol}`", inline=True)
                embed.add_field(
                    name="Atomic Number", value=f"`{atomicnumber}`", inline=True
                )
                embed.add_field(
                    name="Atomic Mass", value=f"`{atomicmass}`", inline=True
                )
                embed.add_field(name="Period", value=f"`{period}`", inline=True)
                embed.add_field(name="Phase", value=f"`{phase}`", inline=True)
                embed.add_field(
                    name="Discoverd By", value=f"`{discovered}`", inline=True
                )
                embed.add_field(name="Summary", value=f"```{summary}```", inline=False)
                embed.set_image(url="attachment://element.png")

                await inter.response.send_message(embed=embed, file=file)

                await inter.response.send_message(embed=embed)
            else:
                await inter.response.send_message(
                    content="Element not found. Please check your input and try again.",
                    ephemeral=True,
                )

        except Exception as e:
            if not inter.response.is_done():
                await inter.response.send_message(content=f"Error: {e}", ephemeral=True)
            else:
                await inter.edit_original_message(content=f"Error: {e}")

    @commands.slash_command(name="colorinfo", description="Get info on a color.")
    async def colorinfo(
        self,
        inter: disnake.ApplicationCommandInteraction,
        hex: str = commands.Param(
            description="Color Hex Code.",
        ),
    ):
        try:
            # Remove the '#' if it's included in the hex code
            hexcode = hex.lstrip("#")

            # Validate the hex code
            if not re.match(r"^[0-9A-Fa-f]{6}$", hexcode):
                await inter.response.send_message(
                    "Invalid hex code. Please provide a valid 6-digit hex code.",
                    ephemeral=True,
                )
                return

            hexcode, name, brightend = color.info(hex)
            r, g, b = color.get_rgb(hex)

            embed = disnake.Embed(
                title="Color Info", color=disnake.Color.from_rgb(r, g, b)
            )
            embed.add_field(name="Hex Code", value=f"#{hex}", inline=True)
            embed.add_field(name="Rgb", value=f"rgb({r}, {g}, {b})", inline=True)
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Brightened", value=brightend, inline=False)

            embed.set_thumbnail(url=f"{config.API_URL}/color/image/{hex}")

            await inter.send(embed=embed)
        except Exception as e:
            print(f"Error processing colorinfo command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error processing colorinfo command: {e}"
                )
            )


def setup(bot):
    bot.add_cog(info(bot))
