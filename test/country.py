async def country1(
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
                    return country.get("famous_for", "Unknown")
            return "Country not found"

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
        famous_for = get_data(country)
        driving_side = data.get("car", {}).get("side", "Unknown")
        area = "{:,} km²".format(data.get("area", 0))
        continents = ", ".join(data.get("continents", "Unknown"))
        tld = data.get("tld", "Unknown")[0]
        landlocked = "Yes" if data.get("landlocked") else "No"
        borders = ", ".join(sorted(data.get("borders", [])))
        if not borders:
            borders = "None"

        shortcode = data.get("cca2", "").lower()
        # image_url = f"https://flagcdn.com/h80/{shortcode}.png"
        image_url = f"https://flagpedia.net/data/flags/h80/{shortcode}.png"

        embed = disnake.Embed(title=f"Country Info for {name}", color=0x36393E)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Capital", value=capital, inline=True)
        embed.add_field(name="Currency", value=currency, inline=True)
        embed.add_field(name="Languages", value=languages, inline=True)
        embed.add_field(name="Phone Code", value=callingcode, inline=True)
        embed.add_field(name="Famous For", value=famous_for.capitalize(), inline=True)
        embed.add_field(name="Driving Direction", value=driving_side, inline=True)
        embed.add_field(name="Area", value=area, inline=True)
        embed.add_field(name="Continent", value=continents, inline=True)
        embed.add_field(name="TLD", value=tld, inline=True)
        embed.add_field(name="Landlocked", value=landlocked, inline=True)
        embed.add_field(name="Neighbours", value=borders.lower(), inline=True)

        embed.set_thumbnail(url=image_url)

        await inter.send(embed=embed)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching country data: {e}")
        await inter.response.send_message("Error fetching country data.")
    except Exception as e:
        print(f"Error processing country command: {e}")
        await inter.response.send_message(
            embed=errors.create_error_embed(f"Error processing country command: {e}")
        )


async def country2(
    self,
    inter: disnake.ApplicationCommandInteraction,
    country: str = commands.Param(
        autocomplete=autocomp_country,
        description="The country to get information on.",
    ),
):
    try:
        # Load country data
        with open("assets/data/countries.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        # Find the country in the data
        country_data = next(
            (c for c in data if c["country"].lower() == country.lower()), None
        )
        if not country_data:
            await inter.response.send_message("Country not found.")
            return

        # Extract relevant information
        name = country_data.get("country", "Unknown")
        capital = country_data.get("capital", "Unknown")
        currency = country_data.get("currency", "Unknown")
        native_language = ", ".join(country_data.get("native_language", ["Unknown"]))
        famous_for = country_data.get("famous_for", "Unknown")
        phone_code = country_data.get("phone_code", "Unknown")
        drive_direction = country_data.get("drive_direction", "Unknown")
        area_km2 = "{:,} km²".format(country_data.get("area", {}).get("km2", 0))
        continent = country_data.get("continent", "Unknown")
        tld = country_data.get("tld", "Unknown")
        landlocked = "Yes" if country_data.get("is_landlocked", False) else "No"
        neighbors = ", ".join(country_data.get("neighbors", ["None"]))

        shortcode = country_data.get("iso", {}).get("alpha_2", "").lower()
        image_url = f"https://flagpedia.net/data/flags/h80/{shortcode}.png"

        embed = disnake.Embed(
            title=f"Country Info for {name.capitalize()}", color=0x36393E
        )
        embed.add_field(name="Name", value=name.capitalize(), inline=True)
        embed.add_field(name="Capital", value=capital.capitalize(), inline=True)
        embed.add_field(name="Currency", value=currency.capitalize(), inline=True)
        embed.add_field(name="Languages", value=native_language, inline=True)
        embed.add_field(name="Phone Code", value=phone_code, inline=True)
        embed.add_field(name="Famous For", value=famous_for.capitalize(), inline=True)
        embed.add_field(name="Driving Direction", value=drive_direction, inline=True)
        embed.add_field(name="Area", value=area_km2, inline=True)
        embed.add_field(name="Continent", value=continent, inline=True)
        embed.add_field(name="TLD", value=tld, inline=True)
        embed.add_field(name="Landlocked", value=landlocked, inline=True)
        embed.add_field(name="Neighbors", value=neighbors, inline=True)
        embed.set_thumbnail(url=image_url)

        await inter.response.send_message(embed=embed)

    except Exception as e:
        print(f"Error processing country command: {e}")
        await inter.response.send_message(f"An error occurred: {e}")
