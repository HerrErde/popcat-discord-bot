import disnake
from disnake.ext import commands

from db import DBHandler
from helpers import errors


class userbio(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Userbio")
        await self.db_handler.initialize()

    @commands.slash_command(name="bio")
    async def userbio(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @userbio.sub_command(name="set", description="Set a Bio for yourself.")
    async def bioset(
        self,
        inter: disnake.ApplicationCommandInteraction,
        bio: str = commands.Param(description="The bio that you want to set."),
    ):
        try:
            user_id = str(inter.author.id)

            await self.db_handler.set_userbio(user_id, bio)

            embed = disnake.Embed(
                title="Set Bio!",
                description=f"Set your bio as `{bio}`",
                color=disnake.Color.blurple(),
            )

        except Exception as e:
            print(f"An error occurred while setting user bio: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Failed to set bio: {e}")
            )
            return

        await inter.response.send_message(embed=embed)

    @userbio.sub_command(name="view", description="View someone elses bio.")
    async def bioview(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(description="The User to get the bio of"),
    ):
        try:
            response = await self.db_handler.get_userbio(user.id)

            embed = disnake.Embed(
                title=f"{user.name}'s Bio!",
                description=f"`{response}`",
                color=disnake.Color.blurple(),
            )

        except Exception as e:
            print(f"An error occurred while setting user bio: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Failed to set bio: {e}")
            )
            return

        await inter.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(userbio(bot))
