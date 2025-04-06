import disnake
from disnake.ext import commands

from db import DBHandler
from helpers import errors
from module import Welcome


class welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Loaded Cog Welcome")
        await self.db_handler.initialize()

    @commands.slash_command(name="welcome-setup")
    @commands.has_permissions(administrator=True)
    async def welcomesetup(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @welcomesetup.sub_command(name="info", description="View how the System works!")
    async def info(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        try:
            embed = disnake.Embed(
                title="Welcome System Setup!",
                description="This Welcoming System Enables You To Greet Members In Your Server In An Epic Way With Welcome Cards! Below are the subcommands you can use to configure the system!",
                colour=disnake.Color.orange(),
            )
            embed.add_field(
                name="`/welcome-setup channel`",
                value="This will set the channel to which the welcome messages and card will be sent.",
                inline=False,
            )
            embed.add_field(
                name="`/welcome-setup message`",
                value="This will be the message sent along with the image!",
                inline=False,
            )
            embed.add_field(
                name="`/welcome-setup disable`",
                value="Disables the welcoming plugin for the server!",
                inline=False,
            )
            embed.add_field(
                name="`/welcome-setup test`",
                value="Try out the welcomer for the server after you've applied settings to see if it works!",
                inline=False,
            )
            embed.add_field(
                name="`Message Customization`",
                value="Include these tags in the message you will set to customize the final message!",
                inline=False,
            )
            embed.add_field(
                name="",
                value="`{member} - Pings the new member \n{member.tag} - Shows the username & tag of the new member without mention \n{member.username} - Username of the member \n{servername} - Name of the server`",
                inline=False,
            )

            await inter.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error sending message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error sending message: {e}")
            )

    @welcomesetup.sub_command(
        name="channel",
        description="This will set the channel to which the welcome messages and card will be sent.",
    )
    async def channel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(
            description="The channel to set the welcome channel to."
        ),
    ):

        await inter.response.defer()
        try:
            guild_id = str(inter.guild.id)
            channel = channel.id
            status = await self.db_handler.set_welcome(guild_id, channel)
            if status:
                response = (
                    f"<a:tick3:1269568991811207211> Welcome Channel Set To <#{channel}>"
                )
            else:  # If the channel is invalid
                response = f":x: Invalid Channel"

            await inter.followup.send(content=response)
        except Exception as e:
            print(f"Error sending message: {e}")
            await inter.inter.followup.send(
                embed=errors.create_error_embed(f"Error sending message: {e}")
            )

    @welcomesetup.sub_command(
        name="message",
        description="This will be the message sent along with the image!",
    )
    async def message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message: str = commands.Param(
            description="The welcome message to be sent with the image."
        ),
    ):

        await inter.response.defer()

        try:
            guild_id = str(inter.guild.id)
            member = inter.author

            # Ensure member is correctly retrieved as a disnake.User object
            if not isinstance(member, disnake.User):
                member = await inter.guild.fetch_member(member.id)

            status = await self.db_handler.set_welcome_msg(guild_id, message)
            if status:
                # Manually replace predefined placeholders
                formatted_message = message.replace(
                    "{member.tag}", f"{member.name}#{member.discriminator}"
                )
                formatted_message = formatted_message.replace(
                    "{member.username}", f"{member.name}"
                )
                formatted_message = formatted_message.replace(
                    "{member}", f"{member.mention}"
                )
                formatted_message = formatted_message.replace(
                    "{servername}", f"{inter.guild.name}"
                )

                response = (
                    f"<a:tick3:1269568991811207211> Welcome Message Set To: `{message}`\n"
                    f"**Preview:** {formatted_message}"
                )
            else:
                response = ":x: Failed to set the welcome message."

            await inter.followup.send(content=response)
        except Exception as e:
            print(f"Error sending message: {e}")
            await inter.followup.send(content=f"Error sending message: {e}")

    @welcomesetup.sub_command(
        name="disable", description="Disable the welcomer for this server."
    )
    async def disable(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):

        await inter.response.defer()

        try:
            guild_id = str(inter.guild.id)
            status = await self.db_handler.remove_welcome(guild_id)
            if status:
                response = f"<a:tick3:1269568991811207211> Deleted Welcomer Data For This Server!"
            else:  # If the welcome data dosnt exsist
                response = (
                    f"How do you expect to disable something that's non existent?"
                )

            await inter.followup.send(content=response)
        except Exception as e:
            print(f"Error sending message: {e}")
            await inter.inter.followup.send(
                embed=errors.create_error_embed(f"Error sending message: {e}")
            )

    @welcomesetup.sub_command(
        name="test",
        description="Test out the welcomer for the server after you've applied settings to see if it works!",
    )
    async def test(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        await inter.response.defer()

        try:
            await inter.followup.send(
                "Attempted to execute welcome event with the guild welcomer data (if there's any)!"
            )
            guild_id = str(inter.guild.id)
            result = await Welcome.welcome(self, inter.user, guild_id)

            # Check if result is None or if any part of it is None
            if result is None:
                return

            response, output_bytes, channel = result

            if response is None or output_bytes is None or channel is None:
                return

            await channel.send(
                content=response,
                file=disnake.File(output_bytes, "welcome.png"),
            )

        except Exception as e:
            print(f"Error sending welcome message: {e}")
            await inter.followup.send(
                "An error occurred while sending the welcome message.",
                ephemeral=True,
            )

    @welcomesetup.error
    async def welcomesetup_error(
        self, inter: disnake.ApplicationCommandInteraction, error
    ):
        if isinstance(error, commands.MissingPermissions):
            await inter.inter.followup.send(
                "Only Administrators Can Use This Command!", ephemeral=True
            )
        else:
            await inter.inter.followup.send(
                f"An error occurred: {str(error)}", ephemeral=True
            )


"""
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            channel = self.bot.get_channel(config.welcome_channel)
            embed = disnake.Embed(
                title=f"Goodbye {member.name}!",
                description=f"Goodbye {member.name}! We hope you enjoyed your stay here!",
                color=disnake.Color.red(),
            )
            embed.add_field(
                name="\nUser Info",
                value=f"\n**User:** ```{member.name}#{member.discriminator} ({member.id})```\n**Account Created:** ```{member.created_at.strftime('%a, %#d %B %Y, %I:%M %p UTC')}```\n**Joined Server:** ```{member.joined_at.strftime('%a, %#d %B %Y, %I:%M %p UTC')}```\n",
                inline=False,
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(
                text=f"{member.guild.name} | {member.guild.member_count} Members",
                icon_url=member.guild.icon.url,
            )
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending goodbye message: {e}")
            await inter.inter.followup.send(
                embed=errors.create_error_embed(f"Error sending goodbye message: {e}")
            )
"""


def setup(bot):
    bot.add_cog(welcome(bot))
