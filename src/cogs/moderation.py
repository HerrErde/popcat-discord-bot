import disnake
from disnake.ext import commands


from db import DBHandler
from helpers import errors


class moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Moderation")
        await self.db_handler.initialize()

    @commands.slash_command(name="warn", description="Warn a user.")
    @commands.has_permissions(administrator=True)
    async def warn(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(description="The user to warn."),
        reason: str = commands.Param(description="Reason for warning."),
    ):

        await inter.response.defer()
        try:
            guild = inter.guild
            guild_id = str(guild.id)
            user_id = str(user.id)
            moderator_id = str(inter.author.id)

            # Check if the moderator's highest role is higher than the user's highest role
            if inter.author.top_role <= user.top_role:
                response = "You cannot perform this action due to your highest role being equal to or lower than the target member's highest role."
                await inter.followup.send(
                    content=response,
                    ephemeral=True,
                )
            else:
                # Add warning to the database
                success = await self.db_handler.add_warning(
                    guild_id, user_id, moderator_id, reason
                )
                if success:
                    warnings_list = await self.db_handler.list_warning(
                        guild_id, user_id
                    )

                    response = f"**{user.name}** has been warned. They now have **{len(warnings_list)}** warning(s) in this server."

                    # Attempt to send a direct message to the warned user
                    try:
                        dm_message = f"You have been warned for **{reason}** in the guild **{guild.name}**."
                        await user.send(dm_message)
                    except disnake.Forbidden:
                        print(
                            f"Failed to send a warning DM to {user.name} (ID: {user_id}) - Missing permissions."
                        )
                        # Inform the moderator if sending DM fails due to permissions
                        response += f"\n\nWarning: Failed to send a direct message to {user.name} about the warning due to privacy settings."

        except Exception as e:
            print(f"An error occurred while processing the command: {e}")
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Failed to execute command: {e}",
                    color=disnake.Color.red(),
                )
            )
            return

        await inter.followup.send(content=response)

    @warn.error
    async def warn_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            await inter.response.send_message(
                "Only Administrators Can Use This Command!", ephemeral=True
            )
        else:
            await inter.response.send_message(
                f"An error occurred: {str(error)}", ephemeral=True
            )

    @commands.slash_command(name="warns", description="Check a user's warns.")
    @commands.has_permissions(administrator=True)
    async def warns(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The user to check warnings for."
        ),
    ):

        await inter.response.defer()
        try:
            guild_id = str(inter.guild.id)
            user_id = str(user.id)

            # get the updated list of warnings
            warnings_list = await self.db_handler.list_warning(guild_id, user_id)

            if warnings_list:
                description = ""
                for idx, warning in enumerate(warnings_list):
                    # Fetch the moderator's user object for each warning
                    moderator = await inter.guild.fetch_member(warning["moderator"])
                    description += f"**{idx + 1}** | Moderator: **{moderator.name}**\nReason: {warning['reason']}\n"

                    embed = disnake.Embed(
                        title=f"{user.name}'s Warnings! [{len(warnings_list)}]",
                        description=description,
                        color=0xFFCC99,
                    )
                    await inter.followup.send(embed=embed)
            else:
                response = f"{user.name} Has No Warns In This Server!"
                await inter.followup.send(content=response, ephemeral=True)

        except Exception as e:
            print(f"An error occurred while fetching from the database: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Failed to fetch from database: {e}")
            )

    @warns.error
    async def warns_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            await inter.response.send_message(
                "Only Administrators Can Use This Command!", ephemeral=True
            )
        else:
            await inter.response.send_message(
                f"An error occurred: {str(error)}", ephemeral=True
            )

    @commands.slash_command(name="removewarn", description="Remove a user's warning.")
    @commands.has_permissions(administrator=True)
    async def removewarn(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(description="The user."),
        number: int = commands.Param(description="The number of warns to remove"),
    ):
        guild_id = inter.guild_id
        guild = inter.guild
        user_id = str(user.id)

        await inter.response.defer()
        try:
            success = await self.db_handler.remove_warning(guild_id, user_id, number)
            if success:
                response = "Successfully deleted the warning!"
                await inter.followup.send(content=response)

                dm_message = f"**{inter.author.name}** has removed your warning in guild {guild.name}"
                await user.send(dm_message)
            else:
                response = f"{user.name} Has No Warns In This Server!"
                await inter.followup.send(content=response, ephemeral=True)

        except Exception as e:
            print(f"An error occurred while fetching from the database: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Failed to fetch from database: {e}"),
                ephemeral=True,
            )
            return

    @removewarn.error
    async def removewarn_error(
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
    bot.add_cog(moderation(bot))
