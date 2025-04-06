import os
from datetime import datetime

import disnake
import humanize
import requests
from disnake.ext import commands, tasks

import config
from db import DBHandler, RedisHandler
from module import Welcome


class Listener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()
        self.message_counts = {}
        self.current_guild = None
        self.redis_client = None

    async def init_redis(self):
        self.redis_client = await RedisHandler().get_client()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Listener")
        await self.db_handler.initialize()

    @commands.Cog.listener()
    async def on_slash_command(self, inter):
        if not inter.guild:
            return

        user_id = inter.author.id
        guild_id = inter.guild.id

        # Construct full command string including subcommands
        full_command = inter.data.name
        if inter.data.options:
            options = " ".join(option["name"] for option in inter.data.options)
            full_command += " " + options

        # Print information about the slash command used
        print(f"Slash command used by {inter.author}: {full_command}")
        # TODO maybe switch to redis cache
        await self.db_handler.inc_user_comm_count(user_id)
        await self.db_handler.inc_guild_comm_count(guild_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return

        await Listener.init_redis(self)

        user_id = message.author.id  # Get the user ID
        await self._handle_message_count_check(message, user_id)
        await self._handle_afk_status(message, user_id)
        await self._handle_chatbot_response(message, user_id)

    async def _handle_message_count_check(self, message, user_id):
        """Checks if the user has sent 20 messages and notifies them of unread updates."""
        # Initialize message count for the user if not already present
        if user_id not in self.message_counts:
            self.message_counts[user_id] = 0
        self.message_counts[user_id] += 1

        # Notify the user if they've sent 20 messages and have unread updates
        if self.message_counts[user_id] >= 20:
            changes_key = f"changes:{user_id}"
            read_changes = await self.redis_client.get(changes_key)

            if not read_changes:
                warning_message = f"{message.author.mention} warning: Unread Update! Use </changes:1114182300222111876> to view!"
                await message.reply(content=warning_message, mention_author=True)

            # Reset the message count for the user
            self.message_counts[user_id] = 0

    async def _handle_afk_status(self, message, user_id):
        """Handles AFK status for the message author and mentioned users."""
        # Check if the author is AFK and remove their AFK status
        afk_status = await self.redis_client.hgetall(f"{user_id}:afk")
        if afk_status:
            await self.redis_client.delete(f"{user_id}:afk")
            response = f"Welcome back, **{message.author.name}**! I have removed your AFK status."
            await message.reply(content=response, mention_author=False)

        # Check if any mentioned users are AFK
        for user in message.mentions:
            afk_status = await self.redis_client.hgetall(f"{user.id}:afk")
            if afk_status:
                reason = afk_status.get("reason")
                stored_timestamp = float(afk_status.get("time"))
                current_timestamp = datetime.datetime.now().timestamp()

                # Calculate and format the time since the user went AFK
                seconds_since = current_timestamp - stored_timestamp
                formatted_time = humanize.naturaldelta(
                    dt.timedelta(seconds=seconds_since)
                )

                response = (
                    f"**{user.name}** is currently AFK: {reason}. {formatted_time}"
                )
                await message.reply(content=response, mention_author=False)

    async def _handle_chatbot_response(self, message, user_id):
        """Generates a chatbot response if the message is in the designated chatbot channel."""
        guild_id = message.guild.id
        channel_id = await self.db_handler.chatbot_get(guild_id)

        # Ignore messages not in the designated chatbot channel
        if message.channel.id != channel_id:
            return

        user_message = message.content

        try:
            response = requests.get(
                f"http://api.brainshop.ai/get?bid={config.BRAINSHOP_ID}&key={config.BRAINSHOP_APIKEY}&uid={user_id}&msg={user_message}"
            )
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            bot_response = response.json().get("cnt")

            if bot_response:
                await message.reply(content=bot_response)
            else:
                print("Bot response is empty.")
        except Exception as e:
            print(f"Error processing message: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            guild_id = str(member.guild.id)
            response, output_bytes, channel = await Welcome.welcome(
                self, member, guild_id
            )
            if not response or not output_bytes or not channel:
                return

            await channel.send(
                content=response,
                file=disnake.File(output_bytes, "welcome.png"),
            )

        except Exception as e:
            print(f"Error sending welcome message: {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self._handle_bot_join(self, guild)
        await self._handle_auto_sharding(self, guild)

    async def _handle_auto_sharding(self, guild):
        if config.AUTO_SHARDING:
            # Get the total number of guilds the bot has joined
            guild_count = len(self.bot.guilds)

            # Check if the guild count is 1000 or more
            if guild_count >= 1000:
                # Create the "SHARDING" file if it does not already exist
                if not os.path.isfile("SHARDING"):
                    with open("SHARDING", "w") as file:
                        pass
                    print("Bot will enable sharding by the next restart")

    async def _handle_bot_join(self, guild):
        print(f"Joined guild: {guild.name} (ID: {guild.id})")

        default_channel = guild.system_channel
        if default_channel:
            embed = disnake.Embed(
                title="Thanks for adding me to your server! :smiling_face_with_3_hearts:",
                description="I am a cool multipurpose discord bot built for making your server better! "
                "I only support slash commands so please use the /help command!",
                color=disnake.Color.random(),
            )
            embed.set_footer(text=f"Enjoy!")
            await default_channel.send(embed=embed)

        # Iterate through each member and upsert economy data
        # Listener.upsert_economy.start()

    @tasks.loop(seconds=5.0, count=1)
    async def upsert_economy(self):
        if self.current_guild:
            print(f"Upserting economy data for members in {self.current_guild.name}")
            for member in self.current_guild.members:
                if not member.bot:
                    try:
                        await self.upsert_economy_for_member(member.id)
                    except Exception as e:
                        print(f"Error upserting economy data for user {member.id}: {e}")

    @upsert_economy.after_loop
    async def after_upsert_economy(self):
        if self.current_guild:
            print(f"Created economy for every user in {guild.name}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if config.AUTO_SHARDING:
            # Get the total number of guilds the bot is currently in
            guild_count = len(self.bot.guilds)

            # Print the guild count for debugging
            print(f"The bot has now joined {guild_count} guilds.")

            # Check if the guild count is less than 1000
            if guild_count < 1000:
                # Remove the "SHARDING" file if it exists
                if os.path.isfile("SHARDING"):
                    os.remove("SHARDING")


"""
    @commands.Cog.listener()
    async def on_slash_command(self, inter):
        # Check if the slash command is invoked by a user (not a bot)
        if inter.author.bot:
            return

        user_id = inter.author.id
        guild_id = inter.guild.id
        channel_id = inter.channel.id

        # Construct full command string including subcommands and options
        full_command = inter.data.name
        options = ""
        if inter.data.options:
            for option in inter.data.options:
                if "value" in option:
                    options += f"{option['name']}:{option['value']} "
                elif "options" in option:
                    sub_options = " ".join(
                        f"{sub_option['name']}:{sub_option['value']}"
                        for sub_option in option["options"]
                        if "value" in sub_option
                    )
                    options += f"{option['name']} {sub_options} "
            full_command += f" {options.strip()}"

        # Print information about the slash command used
        print(
            f"Slash command used:\n"
            f"User ID: {user_id}\n"
            f"Guild ID: {guild_id}\n"
            f"Channel ID: {channel_id}\n"
            f"User: {inter.author}\n"
            f"Full command: {full_command}\n"
            f"Options: {options if options else 'None'}"
        )
"""


def setup(bot):
    bot.add_cog(Listener(bot))
