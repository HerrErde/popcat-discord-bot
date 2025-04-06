import disnake
from disnake.ext import commands

from db import DBHandler


class chatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Chatbot")

    @commands.slash_command(name="chatbot")
    @commands.has_permissions(administrator=True)
    async def chatbot(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @chatbot.sub_command(
        name="set", description="Set the chatbot channel for this server."
    )
    @commands.has_permissions(administrator=True)
    async def set(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(
            description="The channel to set the chatbot channel to."
        ),
    ):
        await inter.response.defer()
        try:
            guild_id = str(inter.guild.id)
            channel_id = channel.id
            success = await self.db_handler.chatbot_set(guild_id, channel_id)

            if success:
                response = f"Set the chatbot channel to <#{channel_id}>"
            else:
                response = f":x: Invalid Channel"

            await inter.followup.send(content=response)

        except Exception as e:
            print(f"Error setting chatbot channel: {e}")
            await inter.followup.send(
                content=f"Error setting chatbot channel: {e}", ephemeral=True
            )

    @chatbot.sub_command(
        name="disable", description="Disable the chatbot for this server."
    )
    @commands.has_permissions(administrator=True)
    async def disable(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        try:
            guild_id = inter.guild.id
            success = await self.db_handler.chatbot_remove(guild_id)

            if success:
                response = "Disabled chatbot module!"
            else:
                response = "Failed to disable chatbot module."

            await inter.followup.send(content=response, ephemeral=True)

        except Exception as e:
            print(f"Error disabling chatbot: {e}")
            await inter.followup.send(
                content=f"Error disabling chatbot: {e}", ephemeral=True
            )

    @chatbot.error
    async def chatbot_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            await inter.response.send_message(
                "Only Administrators Can Use This Command!", ephemeral=True
            )
        else:
            await inter.response.send_message(
                f"An error occurred: {str(error)}", ephemeral=True
            )


def setup(bot):
    bot.add_cog(chatbot(bot))
