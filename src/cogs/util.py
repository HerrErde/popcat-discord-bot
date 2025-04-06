from datetime import datetime

import disnake
from disnake.ext import commands

from db import DBHandler, RedisHandler
from helpers import errors


class util(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()
        self.redis_client = None

    async def init_redis(self):
        self.redis_client = await RedisHandler().get_client()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Util")
        await self.db_handler.initialize()

    @commands.slash_command(
        name="firstmessage", description="View the First Message in this channel."
    )
    async def firstmessage(self, inter: disnake.ApplicationCommandInteraction):
        try:
            async for message in inter.channel.history(limit=1, oldest_first=True):
                embed = disnake.Embed(
                    title="First Message in This Channel!",
                    description=f"Content: {message.content}",
                    color=disnake.Color.blue(),
                )
                embed.add_field(
                    name="Author", value=message.author.mention, inline=True
                )
                embed.add_field(name="Message ID", value=message.id, inline=True)
                embed.add_field(
                    name="Created At",
                    # value=message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    value=message.created_at.strftime("%m/%d/%Y"),
                    inline=True,
                )
                embed.add_field(
                    name="Link",
                    value=f"[Jump To Message!]({message.jump_url})",
                    inline=False,
                )

                # Check if the author has an avatar, else use a default image
                avatar_url = (
                    message.author.avatar.url
                    if message.author.avatar
                    else message.author.default_avatar.url
                )
                embed.set_thumbnail(url=avatar_url)

                await inter.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error retrieving first message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error retrieving first message: {e}")
            )

    @commands.slash_command(
        name="top-invites", description="Get the Top Invites in this Server."
    )
    async def top_invites(self, inter: disnake.ApplicationCommandInteraction):
        try:
            invites = await inter.guild.invites()

            if invites and any(invite.uses > 0 for invite in invites):
                # Sort invites by uses and get the top one
                top_invite = max(invites, key=lambda invite: invite.uses)

                embed = disnake.Embed(
                    title=f"Top Invite in {inter.guild.name}", color=0x1E1F22
                )

                embed.set_author(
                    name=inter.guild.name,
                    icon_url=(
                        inter.guild.icon.url
                        if inter.guild.icon
                        else disnake.Embed.Empty
                    ),
                )

                # Add top invite to embed
                embed.add_field(
                    name="",
                    value=f"- **{top_invite.inviter}'s** invite **{top_invite.code}** has **{top_invite.uses}** uses.",
                    inline=False,
                )

                await inter.response.send_message(embed=embed)
            else:
                await inter.response.send_message(
                    content="There are no invites, or none of them have been used!"
                )
        except Exception as e:
            print(f"Error retrieving invites: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error retrieving invites: {e}")
            )

    @commands.slash_command(name="roleinfo", description="Get Information on a role")
    async def roleinfo(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role = commands.Param(
            description="The role you want to get the info of!"
        ),
    ):
        try:
            embed = disnake.Embed(title="Role Info")
            embed.add_field(name="Name", value=f"<@&{role.id}>", inline=True)
            embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
            embed.add_field(
                name="Position",
                value=f"`{role.position}`/`{len(inter.guild.roles)}`",
                inline=True,
            )
            embed.add_field(
                name="Mentionable",
                value=f"`{'Yes' if role.mentionable else 'No'}`",
                inline=True,
            )
            embed.add_field(
                name="Bot Role",
                value=f"`{'Yes' if role.is_bot_managed() else 'No'}`",
                inline=True,
            )
            embed.add_field(name="Visible", value=f"`{role.hoist}`", inline=True)
            embed.add_field(
                name="Color", value=f"`{str(role.color).upper()}`", inline=True
            )
            embed.add_field(
                name="Creation Date",
                value=f"`{role.created_at.strftime('%d/%b/%Y')}`",
                inline=True,
            )

            # Set the server avatar as the thumbnail if it exists
            if inter.guild.icon:
                embed.set_thumbnail(url=inter.guild.icon.url)

                permissions = {
                    "Administrator": "administrator",
                    "View Audit Log": "view_audit_log",
                    "View Server Insights": "view_guild_insights",
                    "Manage Server": "manage_guild",
                    "Manage Roles": "manage_roles",
                    "Manage Channels": "manage_channels",
                    "Kick Members": "kick_members",
                    "Ban Members": "ban_members",
                    "Create Invite": "create_instant_invite",
                    "Change Nickname": "change_nickname",
                    "Manage Nicknames": "manage_nicknames",
                    "Manage Emojis": "manage_emojis",
                    "Manage Webhooks": "manage_webhooks",
                    "Read Text Channels & See Voice Channels": "read_messages",
                    "Send Messages": "send_messages",
                    "Send TTS Messages": "send_tts_messages",
                    "Manage Messages": "manage_messages",
                    "Embed Links": "embed_links",
                    "Attach Files": "attach_files",
                    "Read Message History": "read_message_history",
                    "Mention @everyone, @here, and All Roles": "mention_everyone",
                    "Use External Emojis": "external_emojis",
                    "Add Reactions": "add_reactions",
                    "Connect": "connect",
                    "Speak": "speak",
                    "Video": "stream",
                    "Mute Members": "mute_members",
                    "Deafen Members": "deafen_members",
                    "Move Members": "move_members",
                    "Use Voice Activity": "use_voice_activation",
                    "Priority Speaker": "priority_speaker",
                }

                permissions_str = "\n".join(
                    [
                        f"{'✔️' if getattr(role.permissions, permission) else '❌'} {permission_name}"
                        for permission_name, permission in permissions.items()
                    ]
                )
                permissions_output = f"```\n{permissions_str}\n```"

                embed.add_field(
                    name="Permissions", value=permissions_output, inline=False
                )

            await inter.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error retrieving role info: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error retrieving role info: {e}")
            )

    @commands.slash_command(name="afk")
    async def afk(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @afk.sub_command(name="set", description="Set your AFK Status")
    async def afk_set(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message: str = commands.Param(description="Your AFK message"),
    ):

        await inter.response.defer()
        try:
            await util.init_redis(self)
            user_id = str(inter.user.id)

            timestamp = int(datetime.now().timestamp())

            await self.redis_client.hmset(
                f"{user_id}:afk",
                {
                    "reason": message,
                    "time": timestamp,
                },
            )

            embed = disnake.Embed(
                description=f"Okay, set your AFK Status to ```{message}```"
            )
            avatar_url = (
                inter.author.avatar.url
                if inter.author.avatar
                else inter.author.default_avatar.url
            )
            embed.set_author(name=inter.author.name, icon_url=avatar_url)
            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error setting afk status: {e}")
            if not inter.response.is_done():
                await inter.followup.send("Error setting afk status.")


def setup(bot):
    bot.add_cog(util(bot))
