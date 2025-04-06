import time

import disnake
from disnake.ext import commands

from db import DBHandler
from helpers import errors


class clicker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Clicker")
        await self.db_handler.initialize()

    @commands.slash_command(name="clicker")
    async def clicker(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @clicker.sub_command(name="create", description="Create the clicker game UI!")
    @commands.has_permissions(administrator=True)
    async def create(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message: str = commands.Param(
            default=None,
            description="The message to show. {count}: click count, {time}: time elapsed, {user}: last clicked by, : newline",
        ),
    ):
        await inter.response.defer()
        try:
            start_time = int(time.time())
            guild_id = str(inter.guild.id)
            total_clicks = await self.db_handler.clicker_total(guild_id)
            last_click_by_id = inter.user.id
            user_cooldowns = {}

            view = disnake.ui.View()
            button = disnake.ui.Button(
                style=disnake.ButtonStyle.red,
                label="Click!",
                emoji="a:popcat_popcorn:1269562318971211817",
                custom_id="click_button",
            )
            view.add_item(button)

            msg = await inter.followup.send(
                content="Created the clicker game UI!",
                ephemeral=True,
            )

            click_msg = await inter.channel.send(
                content="Click the button to start!",
                view=view,
            )

            COOLDOWN_DURATION = 5

            async def button_callback(interaction: disnake.MessageInteraction):
                nonlocal total_clicks, last_click_by_id

                current_time = time.time()
                user_id = str(interaction.user.id)

                # Cooldown check
                if (
                    user_id in user_cooldowns
                    and current_time - user_cooldowns[user_id] < COOLDOWN_DURATION
                ):
                    remaining_time = round(
                        COOLDOWN_DURATION - (current_time - user_cooldowns[user_id])
                    )
                    await interaction.response.send_message(
                        f"You've already clicked recently. Click again in **{remaining_time}s**.",
                        ephemeral=True,
                    )
                    return

                await interaction.response.defer()

                # Update click data
                result = await self.db_handler.clicker_set(guild_id, user_id)
                if result:
                    total_clicks = await self.db_handler.clicker_total(guild_id)
                    last_click_by_id = interaction.user.id
                    user_cooldowns[user_id] = current_time

                    # Format the message
                    formatted_message = (
                        message
                        or "{count} clicks so far!\nLast Clicked by: {user} <t:{time}:R>"
                    )

                    # Replace placeholders in the custom message template
                    new_message = formatted_message.format(
                        count=total_clicks,
                        time=f"<t:{time}:R>",
                        user=interaction.user.mention,
                    )

                    # Edit the original message
                    await click_msg.edit(content=new_message)

            button.callback = button_callback

        except Exception as e:
            print(f"Error creating clicker: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error creating clicker: {e}")
            )

    @clicker.sub_command(
        name="leaderboard", description="Leaderboard for the most clicks in the server!"
    )
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer()
        try:
            guild_id = str(inter.guild.id)

            user_clicks = await self.db_handler.clicker_leaderboard(guild_id)

            if not user_clicks:
                await inter.followup.send("No users found in the leaderboard.")
                return

            sorted_users = sorted(user_clicks.items(), key=lambda x: x[1], reverse=True)

            all_members = await inter.guild.fetch_members(limit=None).flatten()
            user_names = {
                str(
                    member.id
                ): f"{member.name}{'' if member.discriminator == '0' else f'#{member.discriminator}'}"
                for member in all_members
            }

            leaderboard_description = "\n".join(
                f"`{i}.` **{user_names.get(str(user_id), 'Unknown User')}** - {click_count} Clicks"
                for i, (user_id, click_count) in enumerate(sorted_users, 1)
            )

            embed = disnake.Embed(
                title="Click Leaderboard",
                description=leaderboard_description,
                color=disnake.Color.dark_theme(),
            )
            bot_avatar_url = (
                self.bot.user.avatar.url
                if self.bot.user.avatar
                else self.bot.user.default_avatar.url
            )
            embed.set_thumbnail(url=bot_avatar_url)

            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error getting leaderboard: {e}")
            )

    @create.error
    async def clicker_create_error(
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
    bot.add_cog(clicker(bot))
