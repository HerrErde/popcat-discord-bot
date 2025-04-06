import platform
from datetime import datetime, timezone

import disnake
import psutil
from disnake.ext import commands

import config
from db import DBHandler, RedisHandler
from helpers import errors


class general(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()
        self.db_handler = DBHandler()
        self.redis_client = None

    async def init_redis(self):
        self.redis_client = await RedisHandler().get_client()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Loaded Cog General")
        await self.db_handler.initialize()

    @commands.slash_command(
        name="info",
        description="Get information on the bot",
    )
    async def info(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer()
        try:
            command_count = await self.db_handler.com_count_total()
            member_count = len(
                set(
                    member.id
                    for guild in self.bot.guilds
                    for member in guild.members
                    if not member.bot
                )
            )
            embed = disnake.Embed(
                title="Bot Information",
                color=disnake.Color.dark_theme(),
            )
            embed.add_field(
                name=f"❯ {self.bot.user.name}#{self.bot.user.discriminator}",
                value=f"{self.bot.user.id}",
                inline=True,
            )
            embed.add_field(
                name="❯ Servers",
                value=f"{len(self.bot.guilds)}",
                inline=True,
            )
            embed.add_field(
                name="❯ Total Users",
                value=member_count,
                inline=True,
            )
            embed.add_field(
                name="❯ Creation Date",
                value=self.bot.user.created_at.strftime("%dth %B %Y %H:%M:%S"),
                inline=True,
            )
            embed.add_field(
                name="❯ Commands Used",
                value=command_count,
                inline=True,
            )
            embed.add_field(
                name="❯ Python Version",
                value=f"{platform.python_version()}",
                inline=True,
            )
            embed.add_field(
                name="❯ Last Restart",
                value=f"<t:{int(self.start_time.timestamp())}:F>",
                inline=True,
            )
            embed.add_field(
                name="❯ NPM Downloads",
                value="N/A",  # Placeholder
                inline=True,
            )
            embed.add_field(
                name="❯ Donations",
                value="N/A",  # Placeholder
                inline=True,
            )
            bot_user = inter.client.user
            bot_avatar_url = (
                bot_user.avatar.url if bot_user.avatar else bot_user.default_avatar.url
            )
            embed.set_thumbnail(url=bot_avatar_url)

            view = disnake.ui.View()
            api_button = disnake.ui.Button(label="API", url=config.API_URL)
            invite_button = disnake.ui.Button(
                label="Invite",
                url=f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=2483341366&scope=bot%20applications.commands",
            )
            server_button = disnake.ui.Button(label="Server", url="https://discord.gg/")
            donate_button = disnake.ui.Button(
                label="Donate", url="https://ko-fi.com/herrerde"
            )
            view.add_item(api_button)
            view.add_item(invite_button)
            view.add_item(server_button)
            view.add_item(donate_button)

            await inter.followup.send(embed=embed, view=view)

        except Exception as e:
            print(f"Error Sending Info Command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error Sending Info Command: {e}")
            )

    @commands.slash_command(
        name="cpuinfo",
        description="Get information on the bot",
        guild_ids=config.OWNER_GUILD_IDS,
    )
    async def cpuinfo(self, inter: disnake.ApplicationCommandInteraction):
        try:
            embed = disnake.Embed(
                title="Bot Information",
                color=disnake.Color.dark_theme(),
            )

            cpu = psutil.cpu_percent()
            ram_used = psutil.virtual_memory().used / (1024.0**3)
            ram_total = psutil.virtual_memory().total / (1024.0**3)
            storage_used = psutil.disk_usage("/").used / (1024.0**3)
            storage_total = psutil.disk_usage("/").total / (1024.0**3)

            embed.add_field(
                name="❯ CPU Info",
                value=f"`{cpu}% / 100%`",
                inline=False,
            )
            embed.add_field(
                name="❯ RAM Info",
                value=f"`{ram_used:.2f} GB / {ram_total:.2f} GB`",
                inline=False,
            )
            embed.add_field(
                name="❯ Storage Info",
                value=f"`{storage_used:.2f} GB / {storage_total:.2f} GB`",
                inline=False,
            )
            embed.add_field(
                name="❯ Ping",
                value=f"`{round(self.bot.latency * 1000)}ms`",
                inline=False,
            )

            await inter.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error Sending cpuinfo Command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error Sending cpuinfo Command: {e}")
            )

    @commands.slash_command(
        name="ping",
        description="Returns websocket ping",
    )
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        try:
            message = f"{round(self.bot.latency * 1000)}ms!"
            await inter.response.send_message(message)
        except Exception as e:
            print(f"Error Sending Ping Command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error sending ping command: {e}")
            )

    @commands.slash_command(
        name="userinfo",
        description="Get info about a user",
    )
    async def userinfo(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            default=None, description="User to get info on."
        ),
    ):
        user_id = str(inter.author.id)
        try:
            member = user if user else inter.author

            command_count = await self.db_handler.get_user_comm_count(member.id)

            highest_role = member.top_role.mention if member.top_role else "None"

            def day_suffix(day):
                if 4 <= day <= 20 or 24 <= day <= 30:
                    return f"{day}th"
                else:
                    return f"{day}{['st', 'nd', 'rd'][day % 10 - 1]}"

            joined_at = (
                f"{member.joined_at.strftime('%A, %B')} {day_suffix(member.joined_at.day)}, {member.joined_at.year}"
                if member.joined_at
                else "Unknown"
            )
            created_at = f"{member.created_at.strftime('%A, %B')} {day_suffix(member.created_at.day)}, {member.created_at.year}"
            user_bio = await self.db_handler.get_userbio(user_id)
            roles = member.roles[1:]  # Exclude @everyone role
            discriminator = (
                "" if member.discriminator == "0" else f"#{member.discriminator}"
            )

            embed = disnake.Embed(title="", color=0x36393E)
            embed.add_field(
                name="User", value=f"{member.name}{discriminator}", inline=True
            )
            embed.add_field(name="ID", value=f"{member.id}", inline=True)
            embed.add_field(name="Bio", value=user_bio, inline=True)
            embed.add_field(name="Commands Used", value=command_count, inline=True)
            embed.add_field(name="Highest Role", value=f"{highest_role}", inline=True)
            embed.add_field(name="Joined", value=f"{joined_at}", inline=True)
            embed.add_field(name="Created", value=f"{created_at}", inline=False)
            embed.add_field(
                name=f"Roles [{len(roles)}]",
                value=", ".join(role.mention for role in roles),
                inline=False,
            )

            if inter.guild.icon:
                embed.set_thumbnail(url=inter.guild.icon.url)

            await inter.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error sending userinfo message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error sending userinfo message: {e}")
            )

    @commands.slash_command(
        name="serverinfo",
        description="Get info about the server",
    )
    async def serverinfo(self, inter: disnake.ApplicationCommandInteraction):
        try:
            # get server information
            guild = inter.guild
            command_count = await self.db_handler.get_guild_comm_count(inter.guild.id)
            verification_level = (
                inter.guild.verification_level.name
                if inter.guild.verification_level.name and not "none"
                else "None"
            )
            members_count = inter.guild.member_count
            highest_role = (
                f"<@&{inter.guild.roles[-1].id}>" if inter.guild.roles else "None"
            )
            emoji_count = len(inter.guild.emojis)
            partnered = "true" if "PARTNERED" in guild.features else "false"
            verified = "true" if "VERIFIED" in guild.features else "false"
            boosts = inter.guild.premium_subscription_count
            system_channel = (
                inter.guild.system_channel.mention
                if inter.guild.system_channel
                else "None"
            )
            rules_channel = (
                inter.guild.rules_channel.mention
                if inter.guild.rules_channel
                else "None"
            )
            creation_date = inter.guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
            channels_count = len(inter.guild.channels)

            creation_date = inter.guild.created_at.replace(tzinfo=timezone.utc)
            # Calculate the number of days ago
            days_ago = (datetime.now(timezone.utc) - creation_date).days

            # Format the creation date
            creation_date_str = creation_date.strftime("%a, %d %b %Y")

            embed = disnake.Embed(title=f"", color=disnake.Color.dark_theme())
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url)

            embed.add_field(name="Name", value=f"`{inter.guild.name}`", inline=True)
            embed.add_field(name="ID", value=f"`{inter.guild.id}`", inline=True)
            embed.add_field(
                name="Verification Level", value=f"`{verification_level}`", inline=True
            )
            embed.add_field(name="Members", value=f"`{members_count}`", inline=True)
            embed.add_field(name="Highest Role", value=f"{highest_role}", inline=True)
            embed.add_field(name="Emoji Count", value=f"`{emoji_count}`", inline=True)
            embed.add_field(
                name="Commands Used", value=f"`{command_count}`", inline=True
            )
            embed.add_field(name="Partnered", value=f"`{partnered}`", inline=True)
            embed.add_field(name="Verified", value=f"`{verified}`", inline=True)
            embed.add_field(name="Boosts", value=f"`{boosts}`", inline=True)
            embed.add_field(
                name="Roles", value=f"`{len(inter.guild.roles)}`", inline=True
            )
            embed.add_field(
                name="System Channel", value=f"`{system_channel}`", inline=True
            )
            embed.add_field(
                name="Rules Channel", value=f"`{rules_channel}`", inline=True
            )

            embed.add_field(
                name="Creation Date",
                value=f"`{creation_date_str} ({days_ago} days ago)`",
                inline=True,
            )
            embed.add_field(
                name="Channels Count", value=f"Total `{channels_count}`", inline=True
            )
            if inter.guild.icon:
                embed.set_thumbnail(url=inter.guild.icon.url)

            await inter.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error sending serverinfo message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error sending serverinfo command: {e}"
                )
            )

    # TODO not finished
    @commands.slash_command(
        name="changes", description="View all the changes made to the Bot recently!"
    )
    async def changes(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        try:
            await general.init_redis(self)

            user_id = inter.author.id
            changes_key = "changes:viewed_users"
            count_key = "changes:view_count"

            # Check if the user has already viewed the changes
            user_already_viewed = await self.redis_client.sismember(
                changes_key, user_id
            )

            if not user_already_viewed:
                # Add the user ID to the set and increment the view count
                await self.redis_client.sadd(changes_key, user_id)
                view_count = await self.redis_client.incr(count_key)
            else:
                # If the user has already viewed, just get the current view count
                view_count = await self.redis_client.get(count_key)
                if view_count is None:
                    view_count = 0

            changes_data = await self.db_handler.get_changes()
            timestamp = changes_data["timestamp"]
            date = f"<t:{timestamp}:f>"

            embed = disnake.Embed(
                title="Alert From Developer",
                description=f"**Date** - {date}",
                color=disnake.Color.dark_theme(),
            )

            for field_name, field_value in changes_data["fields"].items():
                embed.add_field(name=field_name, value=field_value, inline=False)

            bot_user = inter.client.user
            bot_avatar_url = (
                bot_user.avatar.url if bot_user.avatar else bot_user.default_avatar.url
            )

            embed.set_author(name=bot_user.name, icon_url=bot_avatar_url)
            embed.set_thumbnail(url=bot_avatar_url)
            embed.set_footer(text=f"Read by {view_count} Users")

        except Exception as e:
            print(f"Error getting changes: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error getting changes: {e}", ephemeral=True
                )
            )


def setup(bot):
    bot.add_cog(general(bot))
