import asyncio
import random
import time
from datetime import datetime, timedelta

import config
import disnake
from disnake.ext import commands

from db import DBHandler, RedisHandler
from helpers import errors


class owner(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()
        self.reset_attempts = {}
        self.redis_client = None

    async def init_redis(self):
        self.redis_client = await RedisHandler().get_client()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Owner")
        await self.db_handler.initialize()

    @commands.is_owner()
    @commands.slash_command(name="owner-only", guild_ids=config.OWNER_GUILD_IDS)
    async def owneronly(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @owneronly.sub_command(name="db-get", description="Get a value in the Database.")
    async def dbget(
        self,
        inter: disnake.ApplicationCommandInteraction,
        entry: str = commands.Param(description="Database entry you want to get."),
    ):
        await inter.response.defer(ephemeral=True)

        try:
            # Split the entry into prefix, ID, and path
            prefix, rest = entry.split(".", 1)
            id, path = rest.split(".", 1)

            # Determine dbtype based on prefix
            if prefix.startswith("users"):
                dbtype = 1
            elif prefix.startswith("guilds"):
                dbtype = 2
            else:
                raise ValueError("Invalid prefix")

            # Fetch the value from the database
            success, response = await self.db_handler.db_get(dbtype, id, path)

            success, response = await self.db_handler.db_get(dbtype, id, path)

            if success:
                # Format the response for display
                if isinstance(response, dict):
                    response_str = str(response)
                elif isinstance(response, list):
                    response_str = "\n".join([str(item) for item in response])
                else:
                    response_str = str(response)

                embed = disnake.Embed(
                    title="Success",
                    description=f"Value for `{entry}`:\n```json\n{response_str}\n```",
                    color=disnake.Color.green(),
                )
            else:
                embed = disnake.Embed(
                    title="Failure",
                    description=f"Failed to fetch value for '{entry}': {response.get('error', 'Unknown error')}",
                    color=disnake.Color.red(),
                )

            await inter.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"An error occurred while fetching from the database: {e}")
            embed = disnake.Embed(
                title="Error",
                description=f"Failed to fetch from database: {e}",
                color=disnake.Color.red(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)

    @owneronly.sub_command(name="db-set", description="Set a value in the Database.")
    async def dbset(
        self,
        inter: disnake.ApplicationCommandInteraction,
        entry: str = commands.Param(description="Database entry you want to set."),
        number: bool = commands.Param(description="Is the value a Number?"),
        value: str = commands.Param(description="Set the value in the Database."),
    ):
        await inter.response.defer(ephemeral=True)
        try:
            # Split the entry into prefix, ID, and path
            prefix, rest = entry.split(".", 1)
            id, path = rest.split(".", 1)

            # Determine dbtype based on prefix
            if prefix.startswith("users"):
                dbtype = 1
            elif prefix.startswith("guilds"):
                dbtype = 2
            else:
                raise ValueError("Invalid prefix")

            # Convert value if it's supposed to be a number
            if number:
                if "." in value:
                    try:
                        value = float(value)
                    except ValueError:
                        embed = disnake.Embed(
                            title="Error",
                            description=f"Value '{value}' should be a valid float!",
                            color=disnake.Color.red(),
                        )
                        await inter.followup.send(embed=embed, ephemeral=True)
                        return
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        embed = disnake.Embed(
                            title="Error",
                            description=f"Value '{value}' should be a valid integer!",
                            color=disnake.Color.red(),
                        )
                        await inter.followup.send(embed=embed, ephemeral=True)
                        return

            # Fetch the value from the database
            success, old_value = await self.db_handler.db_set(
                dbtype, id, number, path, value
            )

            if success:
                embed = disnake.Embed(
                    title="Success",
                    description=f"Value for `{entry}` set to: {value}\nPrevious value was: {old_value}",
                    color=disnake.Color.green(),
                )
            else:
                embed = disnake.Embed(
                    title="Failure",
                    description=f"Failed to set value for `{entry}` to `{value}`",
                    color=disnake.Color.red(),
                )
                await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"An error occurred while fetching from the database: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Failed to fetch from database: {e}", ephemeral=True
                )
            )

    @owneronly.sub_command(name="set-money", description="Set a user's money.")
    async def setmoney(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(None, description="The User ID."),
        money: int = commands.Param(
            description="The amount you want to set the user's money to."
        ),
    ):
        await inter.response.defer(ephemeral=True)

        # If user is not provided, use the message author
        if user is None:
            user = inter.author

        user_id = str(user.id)

        try:
            success = await self.db_handler.money_set(user_id, money)
            if success:
                embed = disnake.Embed(
                    title="Success",
                    description=f"Set Money of {user.name} to {money}",
                    color=disnake.Color.green(),
                )
            else:
                embed = disnake.Embed(
                    title="Failure",
                    description=f"Failed to set money for {user.name}.",
                    color=disnake.Color.red(),
                )
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"An error occurred while setting {user.name} money: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Failed to fetch guilds: {e}"),
                ephemeral=True,
            )
            return

    @owneronly.sub_command(name="top-guilds", description="Guild Info.")
    async def topguilds(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        await inter.response.defer(ephemeral=True)
        try:
            # Fetch guild data
            guilds = self.bot.guilds

            # Sort guilds by member count in descending order and get the top 50
            sorted_guilds = sorted(guilds, key=lambda g: g.member_count, reverse=True)[
                :50
            ]

            leaderboard_description = "\n".join(
                f"{idx + 1}) {guild.name} -> {guild.member_count}"
                for idx, guild in enumerate(sorted_guilds)
            )

            embed = disnake.Embed(
                title="Top Guilds",
                description=leaderboard_description,
                color=disnake.Color.blurple(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"An error occurred while fetching guilds: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Failed to fetch guilds: {e}"),
                ephemeral=True,
            )

    @owneronly.sub_command(
        name="db-stats", description="Get the performance stats of the Database."
    )
    async def dbstats(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        await inter.response.defer(ephemeral=True)

        try:
            # Fetch performance metrics from the database handler
            performance = await self.db_handler.check_performance()

            embed = disnake.Embed(
                title="Database Stats",
                description="Performance metrics for the MongoDB database:",
                color=disnake.Color.green(),
            )

            # Add fields with performance metrics
            if "error" in performance:
                embed.add_field(
                    name="Error",
                    value=f"An error occurred: {performance['error']}",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="MongoDB Version",
                    value=performance.get("version", "N/A"),
                    inline=False,
                )
                embed.add_field(
                    name="Cluster Location",
                    value=performance.get("cluster_location", "N/A"),
                    inline=False,
                )
                embed.add_field(
                    name="Ping Time",
                    value=f"{performance.get('ping', 'N/A')} ms",
                    inline=False,
                )
                embed.add_field(
                    name="Write Speed",
                    value=f"{performance.get('write_speed', 'N/A')} ms",
                    inline=False,
                )
                embed.add_field(
                    name="Read Speed",
                    value=f"{performance.get('read_speed', 'N/A')} ms",
                    inline=False,
                )
                embed.add_field(
                    name="Total DB Size",
                    value=f"{performance.get('total_db_size', 'N/A')} bytes",
                    inline=False,
                )

                # Adding individual database sizes
                db_sizes = performance.get("db_sizes", {})
                for db_name, db_size in db_sizes.items():
                    embed.add_field(
                        name=f"Size of {db_name} DB",
                        value=f"{db_size} bytes" if db_size is not None else "N/A",
                        inline=False,
                    )
                await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"An error occurred while fetching from the database: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Failed to fetch from database: {e}", ephemeral=True
                )
            )

    @commands.is_owner()
    @commands.slash_command(
        name="db-reset",
        description="Reset all data in the Database.",
        guild_ids=config.OWNER_GUILD_IDS,
    )
    async def db_reset(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        try:
            current_time = datetime.utcnow()
            user_id = inter.author.id

            # Initialize the attempts list for the user
            if user_id not in self.reset_attempts:
                self.reset_attempts[user_id] = []

            # Remove attempts older than 1 minute
            self.reset_attempts[user_id] = [
                attempt
                for attempt in self.reset_attempts[user_id]
                if attempt > current_time - timedelta(minutes=1)
            ]

            # Add the current attempt
            self.reset_attempts[user_id].append(current_time)

            if len(self.reset_attempts[user_id]) >= 3:
                await self.start_confirmation_process(inter)
                self.reset_attempts[user_id] = (
                    []
                )  # Reset the count after showing buttons
            else:
                attempts_left = 3 - len(self.reset_attempts[user_id])
                embed = disnake.Embed(
                    title="Confirmation Needed",
                    description=f"Please send the command **{attempts_left}** more time(s) within one minute to reset the database.",
                    color=disnake.Color.orange(),
                )
                await inter.followup.send(embed=embed, ephemeral=True, delete_after=30)

        except Exception as e:
            print(f"An error occurred while resetting the database: {e}")
            embed = disnake.Embed(
                title="Error",
                description=f"Failed to reset database: {e}",
                color=disnake.Color.red(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)

    async def start_confirmation_process(self, inter):
        colors = [
            disnake.ButtonStyle.primary,
            disnake.ButtonStyle.success,
            disnake.ButtonStyle.danger,
            disnake.ButtonStyle.secondary,
        ]
        button_press_counts = {
            "btn1": 1,
            "btn2": 1,
            "btn3": 1,
        }  # Times each button must be pressed
        buttons = [
            disnake.ui.Button(
                label=f"Button 1",
                style=random.choice(colors),
                custom_id="btn1",
            ),
            disnake.ui.Button(
                label=f"Button 2",
                style=random.choice(colors),
                custom_id="btn2",
            ),
            disnake.ui.Button(
                label=f"Button 3",
                style=random.choice(colors),
                custom_id="btn3",
            ),
        ]

        random.shuffle(buttons)
        view = disnake.ui.View(timeout=60)
        button_map = {
            button.custom_id: button for button in buttons
        }  # Map custom_id to buttons
        for button in buttons:
            view.add_item(button)

        message = await inter.followup.send(
            content="Please press the buttons in the correct order to reset the database.",
            view=view,
            ephemeral=True,
        )

        def check(interaction):
            return interaction.user == inter.author and interaction.data[
                "custom_id"
            ] in ["btn1", "btn2", "btn3"]

        try:
            interactions = []
            for _ in range(3):
                interaction = await self.bot.wait_for("button_click", check=check)
                interactions.append(interaction)

                button_id = interaction.data["custom_id"]
                button_press_counts[button_id] -= 1
                if button_press_counts[button_id] == 0:
                    button_map[button_id].disabled = True

                await message.edit(
                    view=view
                )  # Update the message with the new button states

                # Acknowledge the button press without additional messages
                await interaction.response.defer()

            correct_order = ["btn1", "btn2", "btn3"]
            user_order = [interaction.data["custom_id"] for interaction in interactions]

            if user_order == correct_order:
                await message.edit(
                    content="Correct order! Proceeding with reset...", view=None
                )
                await self.db_handler.drop_all_collections()
                embed = disnake.Embed(
                    title="Success",
                    description="All databases have been reset.",
                    color=disnake.Color.green(),
                )
                await message.edit(embed=embed, view=None)
            else:
                await message.edit(
                    content="Incorrect order. Reset process aborted.", view=None
                )
        except asyncio.TimeoutError:
            await message.edit(content="Time's up! Reset process aborted.", view=None)

    @commands.slash_command(
        name="economy-setup",
        description="Upsert economy.",
        guild_ids=config.OWNER_GUILD_IDS,
    )
    async def setup(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="Setup the economy of a user.", default=None
        ),
    ):
        await inter.response.defer(ephemeral=True)
        if user is None:
            user = inter.author

        user_id = str(user.id)

        try:
            success, upsert = await self.db_handler.upsert_economy(user_id)

            if success:
                if upsert:
                    embed = disnake.Embed(
                        title="Success",
                        description=f"Setup economy data for {user.name}",
                        color=disnake.Color.green(),
                    )
                else:
                    embed = disnake.Embed(
                        title="Failure",
                        description=f"{user.name} already has the economy data.",
                        color=disnake.Color.orange(),
                    )
            else:
                embed = disnake.Embed(
                    title="Error",
                    description=f"Failed to initialize the setup economy for {user.name}.",
                    color=disnake.Color.red(),
                )
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error getting balance: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error setting economy: {e}"),
            )

    @owneronly.sub_command(
        name="redis-stats", description="Get the performance stats of Redis."
    )
    async def redis_stats(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        await owner.init_redis(self)

        try:
            # Ping time
            start_time = time.time()
            await self.redis_client.ping()
            ping_time = (time.time() - start_time) * 1000  # convert to ms

            # Write speed
            start_time = time.time()
            await self.redis_client.set("test_key", "test_value")
            write_speed = (time.time() - start_time) * 1000  # convert to ms

            # Read speed
            start_time = time.time()
            await self.redis_client.get("test_key")
            read_speed = (time.time() - start_time) * 1000  # convert to ms

            redis_info = await self.redis_client.info()
            total_size = redis_info.get("used_memory_human")
            version = redis_info.get("redis_version")

            embed = disnake.Embed(
                title="Redis Stats",
                description="Performance metrics for the Redis Database:",
                color=disnake.Color.green(),
            )
            embed.add_field(name="Version", value=version, inline=False)
            embed.add_field(name="Ping Time", value=f"{ping_time:.2f} ms", inline=False)
            embed.add_field(
                name="Write Speed", value=f"{write_speed:.2f} ms", inline=False
            )
            embed.add_field(
                name="Read Speed", value=f"{read_speed:.2f} ms", inline=False
            )
            embed.add_field(name="Total Size", value=total_size, inline=False)
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error getting redis stats: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error getting redis stats: {e}")
            )

    @owneronly.sub_command(name="cooldown", description="Get the cooldown of the user")
    async def cooldown(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to view their cooldowns.", default=None
        ),
    ):
        await inter.response.defer(ephemeral=True)
        await owner.init_redis(self)

        if user is None:
            user = inter.author

        user_id = str(user.id)

        embed = disnake.Embed(
            title=f"{user.name}'s Cooldowns", color=disnake.Color.blue()
        )

        try:
            keys = await self.redis_client.keys(f"{user_id}:cooldown:*")
            if not keys:
                embed = disnake.Embed(
                    title="No Cooldowns",
                    description="This user has no active cooldowns.",
                    color=disnake.Color.green(),
                )
                await inter.followup.send(embed=embed, ephemeral=True)

                return

            for key in keys:
                key_str = key.decode("utf-8")
                function_name = key_str.split(":")[-1]
                cooldown_end_str = await self.redis_client.get(key)
                if cooldown_end_str:
                    cooldown_end = datetime.fromisoformat(
                        cooldown_end_str.decode("utf-8")
                    )
                    now = datetime.utcnow()
                    if cooldown_end > now:
                        time_remaining = cooldown_end - now
                        total_seconds = int(time_remaining.total_seconds())

                        weeks, remainder = divmod(total_seconds, 604800)
                        days, remainder = divmod(remainder, 86400)
                        hours, remainder = divmod(remainder, 3600)
                        minutes, seconds = divmod(remainder, 60)

                        remaining_time_str = (
                            f"{weeks}w {days}d {hours}h {minutes}m {seconds}s"
                        )
                        embed.add_field(
                            name=function_name, value=remaining_time_str, inline=False
                        )
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error getting user cooldowns: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error getting user cooldowns: {e}")
            )

    def loadedcogs(self):
        # Fetch the list of loaded cogs
        loaded_cogs = [
            cog.replace("cogs.", "", 1)
            for cog in self.bot.extensions.keys()
            if cog.startswith("cogs.")
        ]
        return loaded_cogs

    async def cog_autocomplete(
        # adding self. will break it
        inter: disnake.ApplicationCommandInteraction,
        user_input: str,
    ):
        bot = inter.bot
        # Get all loaded cogs
        loaded_cogs = [
            cog.replace("cogs.", "", 1)
            for cog in bot.extensions.keys()
            if cog.startswith("cogs.")
        ]
        # Filter cogs based on user input
        cog_list = [cog for cog in loaded_cogs if user_input.lower() in cog.lower()]
        return cog_list[:25]

    # lists cogs
    @commands.is_owner()
    @commands.slash_command(
        name="listcogs",
        description="List all Loaded Cogs",
        guild_ids=config.OWNER_GUILD_IDS,
    )
    async def listcogs(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        try:
            embed = disnake.Embed(
                title="Loaded Cogs",
                description="\n".join(self.loadedcogs()),
                color=disnake.Color.blurple(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"An error occurred while listing cogs.: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"An error occurred while listing cogs: {e}"
                ),
                ephemeral=True,
            )

    @commands.is_owner()
    @commands.slash_command(
        name="reload", description="Reloads a cog", guild_ids=config.OWNER_GUILD_IDS
    )
    async def reload(
        self,
        inter: disnake.ApplicationCommandInteraction,
        cog: str = commands.Param(autocomplete=cog_autocomplete),
    ):
        await inter.response.defer(ephemeral=True)

        try:
            self.bot.reload_extension(f"cogs.{cog}")

            embed = disnake.Embed(
                title="Success",
                description=f"Reloaded `{cog}` successfully.",
                color=disnake.Color.green(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            # Log the error and send an error embed if the reload fails
            print(f"Failed to reload `{cog}`: {e}")
            error_embed = errors.create_error_embed(f"Failed to reload `{cog}`: {e}")
            await inter.followup.send(embed=error_embed, ephemeral=True)

    @commands.is_owner()
    @commands.slash_command(
        name="reloadall",
        description="Reloads all cogs",
        guild_ids=config.OWNER_GUILD_IDS,
    )
    async def reloadall(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        try:
            for cog in self.loadedcogs():
                self.bot.reload_extension(f"cogs.{cog}")
            embed = disnake.Embed(
                title="Success",
                description="Reloaded all cogs",
                color=disnake.Color.green(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Failed to reload cogs because of {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Failed to reload cogs because of {e}"
                ),
                ephemeral=True,
            )

    # load cogs
    @commands.is_owner()
    @commands.slash_command(
        name="load", description="Loads a cog", guild_ids=config.OWNER_GUILD_IDS
    )
    async def load(
        self,
        inter: disnake.ApplicationCommandInteraction,
        cog: str,
    ):
        await inter.response.defer(ephemeral=True)
        try:
            self.bot.load_extension(f"cogs.{cog}")
            embed = disnake.Embed(
                title="Success",
                description=f"Loaded {cog}",
                color=disnake.Color.green(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Failed to load {cog} because of {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Failed to load {cog} because of {e}"),
                ephemeral=True,
            )

    # unload cogs
    @commands.is_owner()
    @commands.slash_command(
        name="unload", description="Unloads a cog", guild_ids=config.OWNER_GUILD_IDS
    )
    async def unload(
        self,
        inter: disnake.ApplicationCommandInteraction,
        cog: str = commands.Param(autocomplete=cog_autocomplete),
    ):
        await inter.response.defer(ephemeral=True)
        try:
            self.bot.unload_extension(f"cogs.{cog}")
            embed = disnake.Embed(
                title="Success",
                description=f"Unloaded {cog}",
                color=disnake.Color.green(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Failed to unload {cog} because of {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Failed to unload {cog} because of {e}"
                ),
                ephemeral=True,
            )

    @commands.slash_command(
        name="shardinfo",
        description="Get information about the bot's shards",
        guild_ids=config.OWNER_GUILD_IDS,
    )
    async def shardinfo(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer(ephemeral=True)

        try:
            if not hasattr(self, "shards") or len(self.shards) <= 1:
                # If the bot is not using shards
                embed = disnake.Embed(
                    title="Shard Information",
                    description="This bot does not have sharding enabled.",
                    color=disnake.Color.dark_theme(),
                )
                await inter.followup.send(embed=embed, ephemeral=True)

                return

            embed = disnake.Embed(
                title="Bot Shard Information",
                color=disnake.Color.dark_theme(),
            )

            shard_id = inter.guild.shard_id if inter.guild else "N/A"
            shard = self.get_shard(shard_id) if shard_id != "N/A" else None

            embed.add_field(
                name="❯ Current Server Shard",
                value=f"Shard ID: {shard_id} / Total Shards: {shard_count}",
                inline=False,
            )

            if shard:
                latency = shard.latency * 1000  # Convert to ms
                total_guilds = sum(1 for g in self.guilds if g.shard_id == shard_id)
                total_users = sum(
                    len(g.members) for g in self.guilds if g.shard_id == shard_id
                )

                embed.add_field(
                    name="❯ Shard Latency",
                    value=f"{latency:.2f} ms",
                    inline=False,
                )
                embed.add_field(
                    name="❯ Guilds in this Shard",
                    value=f"{total_guilds}",
                    inline=False,
                )
                embed.add_field(
                    name="❯ Users in this Shard",
                    value=f"{total_users}",
                    inline=False,
                )

            total_guilds_all_shards = len(self.guilds)
            total_users_all_shards = sum(len(g.members) for g in self.guilds)
            uptime_seconds = time.time() - self.start_time
            uptime_string = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))

            embed.add_field(
                name="❯ Total Guilds",
                value=f"{total_guilds_all_shards}",
                inline=False,
            )
            embed.add_field(
                name="❯ Total Users",
                value=f"{total_users_all_shards}",
                inline=False,
            )
            embed.add_field(
                name="❯ Bot Uptime",
                value=f"{uptime_string}",
                inline=False,
            )

            await inter.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error Sending shardinfo Command: {e}")
            embed = disnake.Embed(
                title="Error",
                description=f"An error occurred while processing the command: {e}",
                color=disnake.Color.red(),
            )
            await inter.followup.send(embed=embed, ephemeral=True)

    @owneronly.error
    async def reload_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, disnake.ext.commands.errors.NotOwner):
            await inter.response.send_message("Owner only command!")
        else:
            error_message = f"An unexpected error occurred: `{str(error)}`"
            if not inter.response.is_done():
                await inter.response.send_message(error_message, ephemeral=True)
            else:
                await inter.followup.send(error_message, ephemeral=True)


def setup(bot):
    bot.add_cog(owner(bot))
