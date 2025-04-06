from datetime import datetime

import disnake
from disnake.ext import commands

from db import DBHandler


class suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Suggestions")
        await self.db_handler.initialize()

    @commands.slash_command(
        name="suggest",
        description="Send a suggestion to this server's suggestions channel!",
    )
    async def suggest(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The Suggestion to send"),
        image: disnake.Attachment = commands.Param(
            default=None, description="An image to attach to the Suggestion"
        ),
    ):

        await inter.response.defer()
        try:

            user = inter.author
            time = datetime.datetime.now().strftime("%H:%M")

            guild_id = str(inter.guild.id)
            channel_id = await self.db_handler.get_suggestion(guild_id)
            channel = self.bot.get_channel(channel_id)

            if channel:
                embed = disnake.Embed(
                    title=user.name, description=text, color=disnake.Color.blurple()
                )
                embed.set_thumbnail(url=user.avatar.url)
                embed.set_footer(text=f"{user.id} • Today at {time}")
                if image:
                    embed.set_image(url=image.url)

                sent_message = await channel.send(embed=embed)
                await sent_message.add_reaction("✅")
                await sent_message.add_reaction("❌")

                message_url = sent_message.jump_url

                view = disnake.ui.View()
                view.add_item(
                    disnake.ui.Button(
                        label="Go to Message",
                        style=disnake.ButtonStyle.link,
                        url=message_url,
                    )
                )

                await inter.followup.send(content="Suggestion sent!", view=view)
            else:
                await inter.followup.send(
                    content="This server has no suggestions channel set! Please contact an administrator to set one!"
                )

        except Exception as e:
            print(f"Error sending suggestion: {e}")
            if not inter.response.is_done():
                await inter.followup.send(
                    content="An error occurred while sending the suggestion."
                )

    @commands.slash_command(name="suggestions")
    @commands.has_permissions(administrator=True)
    async def suggestions(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @suggestions.sub_command(name="set", description="Set the channel for suggestions")
    async def set(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(
            description="The channel to set the suggestions channel to"
        ),
    ):

        await inter.response.defer()
        try:
            guild_id = str(inter.guild.id)

            # Check if the command already exists
            response = await self.db_handler.set_suggestion(guild_id, channel.id)

            if response:
                await inter.followup.send(
                    f"Set the suggestions channel to #{channel.mention}"
                )

        except Exception as e:
            print(f"Error setting channel: {e}")
            if not inter.response.is_done():
                await inter.followup.send("Error setting the suggestions channel.")

    @suggestions.sub_command(
        name="disable", description="Disable the suggestions Module"
    )
    async def disable(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer()
        try:
            guild_id = str(inter.guild.id)

            if await self.db_handler.remove_suggestion(guild_id):
                await inter.followup.send("Disabled suggestions module!")
            else:
                await inter.followup.send(
                    "Can't disable suggestions module, it's not enabled!"
                )

        except Exception as e:
            print(f"Error disabling suggestions: {e}")
            await inter.followup.send("Error deleting command.")

    @suggestions.error
    async def suggestions_error(
        self, inter: disnake.ApplicationCommandInteraction, error
    ):
        if isinstance(error, commands.MissingPermissions):
            await inter.response.send_message(
                "Only Administrators Can Use This Command!", ephemeral=True
            )
        else:
            await inter.response.send_message(
                f"An error occurred: {str(error)}", ephemeral=True
            )


def setup(bot):
    bot.add_cog(suggestions(bot))
