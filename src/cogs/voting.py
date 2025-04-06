import random

import disnake
from disnake.ext import commands

from db import DBHandler
from helpers import errors
from module import Voting


class voting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Voting")

    @commands.slash_command(name="vote")
    async def vote(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @vote.sub_command(name="link", description="Get the voting URL!")
    async def votelink(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer()

        try:
            response = "Below is the URL to vote for me. Just click the button!"

            view = disnake.ui.View()
            topgg = disnake.ui.Button(
                label="Top.gg",
                url=f"https://top.gg/bot/{self.bot.user.id}/vote",
            )
            view.add_item(topgg)

            # Sending the message with the link button
            await inter.followup.send(content=response, view=view)

        except Exception as e:
            print(f"Error getting link: {e}")
            await inter.followup.sens(
                embed=errors.create_error_embed(f"Error getting link: {e}")
            )

    @vote.sub_command(
        name="rewards", description="Get rewards for voting for me on top.gg"
    )
    async def voterewards(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        bot_id = str(inter.bot.user.id)
        user_id = str(inter.author.id)

        try:
            success, voted, diff = await Voting.vote_get(bot_id, user_id)
            if success and voted:
                if diff > 1:
                    # Generate the random amount for each difference and sum them up
                    total_amount = 0
                    min_amount = 1000
                    max_amount = 3000

                    for _ in range(difference):
                        amount = random.randint(min_amount, max_amount)
                        total_amount += amount
                else:
                    # Generate a random amount between min_amount and max_amount
                    min_amount = 1000
                    max_amount = 3000
                    amount = random.randint(min_amount, max_amount)

                items = [
                    ("Cat", "A Cat! :cat2:", 0.35),  # 35%
                    ("Car", "A Car! :blue_car:", 0.2),  # 20%
                    ("Mansion", "A Mansion! :homes:", 0.01),  # 1%
                    ("Minecraft", "Minecraft! :pick:", 0.2),  # 20%
                    (
                        "Fishing Rod",
                        "A Fishing Rod! :fishing_pole_and_fish:",
                        0.15,
                    ),  # 15%
                    ("Laptop", "A Laptop! :computer:", 0.20),  # 25%
                    ("", "", 0.50),  # 50%
                ]

                weighted_items = [
                    item for item in items for _ in range(int(item[2] * 100))
                ]

                # Choose a random item based on weights
                chosen_item = random.choice(weighted_items)
                item_name, message, _ = next(
                    item for item in items if item[0] == chosen_item
                )

                # Process the reward
                success, exists = await self.db_handler.money_rewards(
                    user_id, item, amount
                )

                if not success:
                    await inter.followup.send(
                        content="There was an error processing your request. Please try again later."
                    )
                    return

                # Prepare the response message
                if not item or not exists:
                    item_message = ""
                else:
                    item_message = f" + {message}"
                if diff > 1:
                    response = f"You have voted for me on top.gg {diff} times! You get: {amount} <:coin:1270075840901812304>{item_message}"
                else:
                    response = f"You have voted for me on top.gg! You get: {amount} <:coin:1270075840901812304>{item_message}"
                view = None
            else:
                response = "You need to vote me on top.gg to get rewards!"

                view = disnake.ui.View()
                topgg = disnake.ui.Button(
                    label="Vote",
                    url=f"https://top.gg/bot/{self.bot.user.id}/vote",
                )
                view.add_item(topgg)

                # Sending the message with the link button
            await inter.followup.send(content=response, view=view)

        except Exception as e:
            print(f"Error getting reward: {e}")
            error_message = f"Error getting reward: {e}"
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error getting reward: {e}")
            )


def setup(bot):
    bot.add_cog(voting(bot))
