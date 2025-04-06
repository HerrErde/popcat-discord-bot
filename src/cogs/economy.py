import random
import re
from datetime import datetime, timedelta

import disnake
from disnake.ext import commands

from db import DBHandler, RedisHandler
from helpers import errors


class CooldownManager:
    def __init__(self):
        self.redis_client = None

    async def init_redis(self):
        self.redis_client = await RedisHandler().get_client()

    # TODO change to disnake cooldown
    async def set_cooldown(self, inter, user_id, function_name, cooldown_str):
        await cooldown_manager.init_redis()
        now = datetime.utcnow()

        time_pattern = re.compile(
            r"(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
        )
        match = time_pattern.fullmatch(cooldown_str)

        if match:
            weeks, days, hours, minutes, seconds = map(
                lambda x: int(x) if x else 0, match.groups()
            )
            # Calculate the total cooldown time
            cooldown_duration = timedelta(
                weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds
            )
        else:
            await print("Invalid cooldown format. Use 'Xw Xd Xh Xm Xs'.")
            return False

        cooldown_key = f"{user_id}:cooldown:{function_name}"
        expiration_time = now + cooldown_duration

        # Check if the cooldown is already active
        current_cooldown = await self.redis_client.get(cooldown_key)
        if current_cooldown:
            current_cooldown = datetime.fromisoformat(current_cooldown.decode("utf-8"))
            if current_cooldown > now:
                time_remaining = current_cooldown - now
                total_seconds = int(time_remaining.total_seconds())

                # Calculate weeks, days, hours, minutes, and seconds from total_seconds
                weeks, remainder = divmod(total_seconds, 604800)
                days, remainder = divmod(remainder, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)

                await print(
                    f"Cooldown active. Time remaining: {weeks}w {days}d {hours}h {minutes}m {seconds}s."
                )
                return False

        # Set the new cooldown time for the function in Redis
        await self.redis_client.setex(
            cooldown_key,
            int(cooldown_duration.total_seconds()),
            expiration_time.isoformat(),
        )
        return True

    async def get_cooldown(self, inter, user_id, function_name, error_message=""):
        await cooldown_manager.init_redis()
        now = datetime.utcnow()
        cooldown_key = f"{user_id}:cooldown:{function_name}"

        current_cooldown = await self.redis_client.get(cooldown_key)
        if current_cooldown:
            current_cooldown = datetime.fromisoformat(current_cooldown.decode("utf-8"))
            if current_cooldown > now:
                time_remaining = current_cooldown - now
                total_seconds = int(time_remaining.total_seconds())

                # Calculate weeks, days, hours, minutes, and seconds from total_seconds
                weeks, remainder = divmod(total_seconds, 604800)
                days, remainder = divmod(remainder, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)

                # Format the error message to include the remaining time
                formatted_message = error_message.format(
                    weeks=weeks,
                    days=days,
                    hours=hours,
                    minutes=minutes,
                    seconds=seconds,
                )
                return True, formatted_message

        # No cooldown or cooldown expired
        return False, ""


cooldown_manager = CooldownManager()


class economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Economy")
        await self.db_handler.initialize()

    @commands.slash_command(name="leaderboard")
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @leaderboard.sub_command(
        name="pocket", description="View the leaderboard for the money in pocket."
    )
    async def leaderboard_pocket(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):

        await inter.response.defer()

        try:

            user_coins = await self.db_handler.list_leaderboard_pocket()

            if not user_coins:
                await inter.followup.send("No users found in the leaderboard.")
                return

            # Sort user_coins by total_pocket in descending order
            sorted_users = sorted(user_coins.items(), key=lambda x: x[1], reverse=True)

            # Fetch all members of the guild and map their display names
            all_members = await inter.guild.fetch_members(limit=None).flatten()
            user_names = {
                str(
                    member.id
                ): f"{member.name}{'' if member.discriminator == '0' else f'#{member.discriminator}'}"
                for member in all_members
            }

            leaderboard_description = "\n".join(
                f"`{i}.` **{user_names.get(str(user_id), 'Unknown User')}** - {total_pocket:,.0f} <:coin:1270075840901812304>"
                for i, (user_id, total_pocket) in enumerate(sorted_users, 1)
            )

            embed = disnake.Embed(
                title="Pop Coins Leaderboard",
                description=leaderboard_description,
                color=0xFFCC99,
            )
            bot_avatar_url = (
                self.bot.user.avatar.url
                if self.bot.user.avatar
                else self.bot.user.default_avatar.url
            )
            embed.set_thumbnail(url=bot_avatar_url)

            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error creating pocket leaderboard: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"Error creating pocket leaderboard: {e}"
                )
            )

    @leaderboard.sub_command(
        name="bank", description="View the leaderboard for the money in bank."
    )
    async def leaderboard_bank(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):

        await inter.response.defer()

        try:
            user_coins = await self.db_handler.list_leaderboard_bank(inter.author.id)

            if not user_coins:
                await inter.followup.send("No users found in the leaderboard.")
                return

            # Sort user_coins by total_bank in descending order
            sorted_users = sorted(user_coins.items(), key=lambda x: x[1], reverse=True)

            # Fetch all members of the guild and map their display names
            all_members = await inter.guild.fetch_members(limit=None).flatten()
            user_names = {
                str(
                    member.id
                ): f"{member.name}{'' if member.discriminator == '0' else f'#{member.discriminator}'}"
                for member in all_members
            }

            leaderboard_description = "\n".join(
                f"`{i}.` **{user_names.get(str(user_id), 'Unknown User')}** - {total_pocket:,.0f} <:coin:1270075840901812304>"
                for i, (user_id, total_pocket) in enumerate(sorted_users, 1)
            )

            embed = disnake.Embed(
                title="Pop Coins Leaderboard",
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
            print(f"Error creating bank leaderboard: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error creating bank leaderboard: {e}")
            )

    @commands.slash_command(name="beg", description="Earn some coins by begging.")
    async def beg(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer()

        user_id = str(inter.author.id)
        min_amount = 5  # Minimum amount of coins a user can beg for
        max_amount = 100  # Maximum amount of coins a user can beg for

        try:
            cooldown, cooldown_msg = await cooldown_manager.get_cooldown(
                inter,
                user_id,
                "beg",
                "You've already begged recently. Beg again in **{seconds}s**",
            )
            if cooldown:
                await inter.followup.send(cooldown_msg)
                return

            # Generate a random amount between min_amount and max_amount
            amount = random.randint(min_amount, max_amount)

            # Update user's balance
            success = await self.db_handler.money_give(user_id, amount)

            if success:
                await cooldown_manager.set_cooldown(inter, user_id, "beg", "5s")
                response = (
                    f"You begged and received **{amount}** <:coin:1270075840901812304>!"
                )
                await inter.followup.send(content=response)
            else:
                await inter.followup.send(
                    content="There was an error processing your request. Please try again later."
                )

        except Exception as e:
            print(f"Error with beg command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"An error occurred while processing your request: {e}"
                )
            )

    @commands.slash_command(name="bal", description="View a user's balance.")
    async def balance(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to view their balance of.", default=None
        ),
    ):
        await inter.response.defer()

        if user is None:
            user = inter.author

        user_id = str(user.id)

        try:
            pocket, bank = await self.db_handler.money_balance(user_id)

            networth = pocket + bank

            # Formatting the numbers
            pocket_formatted = "{:,}".format(pocket)
            bank_formatted = "{:,}".format(bank)
            networth_formatted = "{:,}".format(networth)

            embed = disnake.Embed(
                title="",
                description=f"**{user.name}#{user.discriminator}'s Balance**",
                color=0x57F288,
            )
            embed.add_field(
                name="",
                value=f"\nPocket: **{pocket_formatted}** <:coin:1270075840901812304>\nBank: **{bank_formatted}** <:coin:1270075840901812304>\nNet Worth: **{networth_formatted}** <:coin:1270075840901812304>",
            )

            await inter.followup.send(embed=embed)

        except KeyError as e:
            print(f"KeyError getting balance: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"KeyError getting balance: {e}")
            )
        except Exception as e:
            print(f"Error getting balance: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error getting balance: {e}")
            )

    @commands.slash_command(name="work", description="Work for a payment of coins!")
    async def work(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

        # Possible outcomes
        outcomes = [
            "You got fired from the job, but while leaving you got **{amount}** <:coin:1270075840901812304> from your desk!",
            "Boss: You suck anyways, so you won't be able to earn anything. So here take **{amount}** <:coin:1270075840901812304> as an offering.",
            "You collaborated with Pop Cat and earned **{amount}** <:coin:1270075840901812304>!",
            "You went and cleaned the sewage system, earning **1514** <:coin:1270075840901812304>!",
            "You fed Pop Cat and Pop Cat gives you **{amount}** <:coin:1270075840901812304>!",
        ]

        user_id = str(inter.author.id)
        amount = random.randint(500, 2000)
        reason = random.choice(outcomes).format(amount=amount)

        try:
            cooldown, cooldown_msg = await cooldown_manager.get_cooldown(
                inter,
                user_id,
                "work",
                "You've already worked recently. Please work again in **{minutes}m {seconds}s** : )",
            )
            if cooldown:
                await inter.followup.send(cooldown_msg)
                return

            # Update user's balance
            await cooldown_manager.set_cooldown(inter, user_id, "work", "30m")
            await self.db_handler.money_give(user_id, amount)

            time = datetime.now().strftime("%H:%M")
            embed = disnake.Embed(
                title="",
                description=reason,
                color=disnake.Color.green(),
            )
            embed.set_author(
                name="Your Work",
                icon_url=inter.author.avatar.url if inter.author.avatar else None,
            )
            embed.set_footer(text=f"Today at {time}")
            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error with work command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"An error occurred while processing your work request: {e}"
                )
            )

    @commands.slash_command(name="daily", description="Get your daily coins.")
    async def daily(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        user_id = str(inter.author.id)
        amount = 2000  # Amount of daily reward

        try:
            success, cooldown_time = await self.db_handler.money_daily(user_id, amount)

            if success:
                response = f"You've collected your daily reward of **{amount}** <:coin:1270075840901812304>!"
                await inter.followup.send(content=response)
            else:
                hours, minutes, seconds = cooldown_time
                embed = disnake.Embed(
                    title="You've already collected your daily reward",
                    description=f"Collect it again in **{hours}**h **{minutes}**m **{seconds}**s",
                    color=disnake.Color.red(),
                )
                await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error collecting daily reward: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error collecting daily reward: {e}")
            )

    @commands.slash_command(
        name="slots", description="Bet your money on the slots machine!"
    )
    async def slots(
        self,
        inter: disnake.ApplicationCommandInteraction,
        amount: int = commands.Param(
            description="The amount of coins you want to bet."
        ),
    ):

        await inter.response.defer()
        user_id = str(inter.author.id)

        try:
            # Validate the bet amount
            if amount <= 0:
                await inter.followup.send(
                    content="You can't bet a negative or 0 amount of coins!"
                )
                return

            # Check user balance
            pocket_balance, _ = await self.db_handler.money_balance(user_id)
            if amount > pocket_balance:
                await inter.followup.send(content="You're betting more than you have!")
                return

            slots = ["🍒", "🍋", "🍊", "🍉", "🍇"]
            result = [random.choice(slots) for _ in range(3)]

            # Determine win or loss (all three slots match)
            if result[0] == result[1] == result[2]:
                # Win scenario
                win_amount = amount * 2
                if await self.db_handler.money_slots(user_id, win_amount, is_win=True):
                    embed = disnake.Embed(
                        title="You Won!",
                        description=f":Pop_Vibe: | You won {win_amount} Pop Coins!\n{result[0]} {result[1]} {result[2]}",
                        color=disnake.Color.brand_green(),
                    )
                else:
                    raise Exception("Transaction failed during winning scenario.")
            else:
                # Loss scenario
                if await self.db_handler.money_slots(user_id, amount, is_win=False):
                    embed = disnake.Embed(
                        title="You Lost!",
                        description=f":popcat_triggered: | You lost {amount} Pop Coins.\n{result[0]} {result[1]} {result[2]}",
                        color=disnake.Color.brand_red(),
                    )
                else:
                    raise Exception("Transaction failed during losing scenario.")

            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error with slots command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"An error occurred while processing your slot machine bet: {e}"
                )
            )

    @commands.slash_command(name="give", description="Share your money with others!")
    async def give(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The user you want to give money to."
        ),
        amount: int = commands.Param(
            description="The amount of coins you want to give."
        ),
    ):

        await inter.response.defer()

        user1_id = str(inter.author.id)
        user2_id = str(user.id)

        try:
            # Check if user has enough money before deferring response
            if amount <= 0:
                await inter.response.send_message(
                    content="You can't share a negative or 0 amount of coins!"
                )
                return

            if user1_id == user2_id:
                await inter.response.send_message(
                    content="You can't share money with yourself!"
                )
                return

            # Attempt to give money
            success = await self.db_handler.money_move(user1_id, user2_id, amount)

            if success:
                response = f"Successfully shared **{amount}** <:coin:1270075840901812304> with **{user.display_name}**."
                try:
                    dm_message = f"**{inter.author.name}** has shared {amount} <:coin:1270075840901812304> with you!"
                    await user.send(dm_message)
                except disnake.Forbidden:
                    print(
                        f"Failed to send money info DM to {user.name} (ID: {user2_id}) - Missing permissions."
                    )
            else:
                response = "You don't have that much money."

            await inter.followup.send(content=response)
        except Exception as e:
            print(f"Error transferring money: {e}")
            await inter.response.send_message(
                content="An error occurred while processing your request."
            )

    @commands.slash_command(name="deposit", description="Deposit coins into your bank.")
    async def deposit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        amount: int = commands.Param(
            description="The amount of coins you want to deposit."
        ),
    ):

        await inter.response.defer()
        user_id = str(inter.author.id)

        try:
            # Check if user has enough money before deferring response
            if amount <= 0:
                await inter.followup.send(
                    content="You can't deposit a negative or 0 amount of coins!"
                )

            # Attempt to give money
            success = await self.db_handler.money_deposit(user_id, amount)

            if success:
                response = f"Successfully deposited **{amount}** <:coin:1270075840901812304> into your bank"
            else:
                response = "Don't try to fool me, You don't have that much money."

            await inter.followup.send(content=response)
        except Exception as e:
            print(f"Error making deposit: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error making deposit: {e}")
            )

    @commands.slash_command(
        name="withdraw", description="Withdraw coins from you bank."
    )
    async def withdraw(
        self,
        inter: disnake.ApplicationCommandInteraction,
        amount: int = commands.Param(
            description="The amount of coins you want to withdraw."
        ),
    ):

        await inter.response.defer()
        user_id = str(inter.author.id)

        try:
            # Check if user has enough money before deferring response
            if amount <= 0:
                await inter.response.send_message(
                    content="You can't withdraw a negative or 0 amount of coins!"
                )
                return

            # Attempt to give money
            success = await self.db_handler.money_withdraw(user_id, amount)

            if success:
                response = f"Successfully withdrew **{amount}** <:coin:1270075840901812304> from your bank"
            else:
                response = "Don't try to fool me, You don't have that much money"

            await inter.followup.send(content=response)

        except Exception as e:
            print(f"Error making withdraw: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error making withdraw: {e}")
            )

    @commands.slash_command(name="shop", description="View the store.")
    async def shop(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer()
        try:
            embed = disnake.Embed(title="The Pop Cat Superstore", color=0xD4C5A2)

            embed.add_field(
                name="Cat — 1000 <:coin:1270075840901812304>",
                value="Buy A Cat, And It Blesses You With 1000 Pop Coins Daily!",
                inline=False,
            )
            embed.add_field(
                name="Car — 5000 <:coin:1270075840901812304>",
                value="Use A Car To Go Drivin' And Earn Upto 10000 Pop Coins!",
                inline=False,
            )
            embed.add_field(
                name="Mansion — 20000 <:coin:1270075840901812304>",
                value="Buy A Mansion And You Can Rent It Out To People And Collect An Amount Anywhere From 2000 To 30000 Pop Coins Weekly!",
                inline=False,
            )
            embed.add_field(
                name="Minecraft — 50 <:coin:1270075840901812304>",
                value="Play Minecraft And Win Money!",
                inline=False,
            )
            embed.add_field(
                name="Laptop — 10000 <:coin:1270075840901812304>",
                value="Buy A Laptop And Use It To Post Memes!",
                inline=False,
            )
            embed.add_field(
                name="Rod — 5000 <:coin:1270075840901812304>",
                value="Go Out On The Beach Fishing And Get A Chance To Catch Some Fish!",
                inline=False,
            )

            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error getting shop: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error getting shop: {e}")
            )

    @commands.slash_command(name="buy", description="Buy items from the store.")
    async def buy(
        self,
        inter: disnake.ApplicationCommandInteraction,
        item: str = commands.Param(
            choices=["Cat", "Car", "Mansion", "Minecraft", "Fishing Rod", "Laptop"],
            description="The item you want to buy.",
        ),
    ):
        await inter.response.defer()

        item_prices = {
            "Cat": 1000,
            "Car": 5000,
            "Mansion": 20000,
            "Minecraft": 50,
            "Fishing Rod": 5000,
            "Laptop": 10000,
        }

        if item not in item_prices:
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Invalid item selected: {e}")
            )
            return

        amount = item_prices[item]
        user_id = str(inter.author.id)

        try:
            success, item_added = await self.db_handler.money_buy_item(
                user_id, item.lower(), amount
            )
            if success:
                if item_added:
                    description = (
                        f"Successfully bought a **{item}** for **{amount}** Pop Coins!"
                    )
                    embed = disnake.Embed(
                        title="Purchase Successful",
                        description=description,
                        color=disnake.Color.green(),
                    )

                await inter.send(embed=embed)
            else:
                embed = disnake.Embed(
                    title="Purchase Failed",
                    description="Failed to complete the purchase. Please check your balance.",
                    color=disnake.Color.red(),
                )
                await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error processing buy command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"An error occurred: {e}")
            )

    @commands.slash_command(name="use", description="Use items bought from the shop!")
    async def use(
        self,
        inter: disnake.ApplicationCommandInteraction,
        item: str = commands.Param(
            choices=["Cat", "Car", "Mansion", "Minecraft", "Fishing Rod"],
            description="The item you want to use.",
        ),
    ):
        await inter.response.defer()
        user_id = str(inter.author.id)

        async def use_fishing_rod(inter, user_id):
            cooldown, cooldown_msg = await cooldown_manager.get_cooldown(
                inter,
                user_id,
                "fishing",
                "You can only catch a fish once every minute!\nTry again in **{seconds}s**",
            )
            if cooldown:
                await inter.followup.send(cooldown_msg)
                return

            # Check if the user has a Fishing Rod
            has_item = await self.db_handler.money_check_inv(user_id, "Fishing Rod")
            if not has_item:
                await inter.followup.send(
                    "You don't have a Fishing Rod! Buy it from `/shop` first!"
                )
                return

            # Generate random amount of fish
            amount = random.randint(0, 5)

            # Simulate fishing process
            success = await self.db_handler.money_add_fish(user_id, amount)
            if amount == 0:
                outcome = "You fell into the water while trying to fish XD"
            else:
                success = await self.db_handler.money_add_fish(user_id, amount)
                if success:
                    # Update cooldown
                    await cooldown_manager.set_cooldown(inter, user_id, "fishing", "1m")
                    outcome = random.choice(
                        [
                            f"You jump into the water and grab {amount} :fish:",
                            f"You fished and got {amount} :fish:",
                            f"You throw your bait into the water and come back with {amount} :fish:",
                            f"You cast out your line {amount} :fish:",
                        ],
                    )

                await inter.followup.send(outcome)

        async def use_cat(inter, user_id):
            cooldown, cooldown_msg = await cooldown_manager.get_cooldown(
                inter,
                user_id,
                "cat",
                "Don't Try To Be Greedy. Your Cat Will Only Bless You Once A Day! Please come back **{hours}**h **{minutes}**m **{seconds}**s",
            )
            if cooldown:
                await inter.followup.send(cooldown_msg)
                return

            has_item = await self.db_handler.money_check_inv(user_id, "Cat")
            if not has_item:
                await inter.followup.send(
                    "You don't own a Cat! Buy it from `/shop` first!"
                )
                return

            amount = 1000

            # Simulate fishing process
            success = await self.db_handler.money_give(user_id, amount)
            if success:
                # Update cooldown
                await cooldown_manager.set_cooldown(inter, user_id, "cat", "1d")

                embed = disnake.Embed(
                    title="Success",
                    description=f"You Pat Your Cat, And It Blesses You With {amount} <:coin:1270075840901812304>",
                    color=disnake.Color.brand_green(),
                )

                embed.set_footer(text=f"Cat Owner: {inter.user.name}")
                await inter.followup.send(embed=embed)

        async def use_car(inter, user_id):
            cooldown, cooldown_msg = await cooldown_manager.get_cooldown(
                inter,
                user_id,
                "car",
                "You can't be on the road all day! Go on a drive again in **{hours}**h **{minutes}**m **{seconds}**s",
            )
            if cooldown:
                embed = disnake.Embed(
                    title="Slow Down...",
                    description=cooldown_msg,
                    color=disnake.Color.brand_red(),
                )
                await inter.followup.send(embed=embed)
                return

            has_item = await self.db_handler.money_check_inv(user_id, "Car")
            if not has_item:
                await inter.followup.send(
                    "You don't own a Car! Buy it from `/shop` first!"
                )
                return

            # Generate random amount of money
            amount = random.randint(5000, 9000)

            # Simulate fishing process
            success = await self.db_handler.money_give(user_id, amount)
            if success:
                # Update cooldown
                await cooldown_manager.set_cooldown(inter, user_id, "car", "10h")

                embed = disnake.Embed(
                    title="Success",
                    description=f"You Went On A Drive With Your Cat, Earning {amount} <:coin:1270075840901812304>",
                    color=disnake.Color.brand_green(),
                )

                embed.set_footer(text=f"Car Owner: {inter.user.name}")
                await inter.followup.send(embed=embed)

        async def use_minecraft(inter, user_id):
            cooldown, cooldown_msg = await cooldown_manager.get_cooldown(
                inter,
                user_id,
                "minecraft",
                "Woaah, slow down there. You already played minecraft for hours last night and you wanna play it again?! Come back in **{seconds}**s",
            )
            if cooldown:
                await inter.followup.send(cooldown_msg)
                return

            has_item = await self.db_handler.money_check_inv(user_id, "Minecraft")
            if not has_item:
                await inter.followup.send(
                    "You don't own a copy of Minecraft! Buy it from `/shop` first!"
                )
                return

            # Generate random amount of money
            amount = random.randint(10, 500)

            # Simulate fishing process
            success = await self.db_handler.money_give(user_id, amount)
            if success:
                # Update cooldown
                await cooldown_manager.set_cooldown(inter, user_id, "minecraft", "1m")

                await inter.followup.send(
                    f"You Played Minecraft For The Entire Night. It was so good that you're {amount} <:coin:1270075840901812304> richer now!"
                )

        async def use_mansion(inter, user_id):
            # Generate random amount of rent
            amount = random.randint(10000, 30000)

            # Simulate rent collection process
            success, cooldown = await self.db_handler.money_mansion(user_id, amount)
            if success:
                if isinstance(cooldown, bool):
                    if cooldown is False:
                        await inter.followup.send(
                            "You don't have a Mansion! Buy it from `/shop` first!"
                        )
                    else:

                        embed = disnake.Embed(
                            title="Payment Success",
                            description=f"Your tenant paid you a rent of {amount} <:coin:1270075840901812304>",
                            color=disnake.Color.brand_green(),
                        )

                        embed.set_footer(text=f"Mansion Owner: {user.name}")
                        await inter.followup.send(embed=embed)
                else:
                    await inter.followup.send(
                        f"You can only collect rent from the tenants once a week!\n"
                        f"Try again in **{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s**"
                    )
                    return
            else:
                await inter.followup.send("Unexpected Error")

        try:
            item_actions = {
                "Fishing Rod": lambda inter, user_id: use_fishing_rod(inter, user_id),
                "Cat": lambda inter, user_id: use_cat(inter, user_id),
                "Car": lambda inter, user_id: use_car(inter, user_id),
                "Mansion": lambda inter, user_id: use_mansion(inter, user_id),
                "Minecraft": lambda inter, user_id: use_minecraft(inter, user_id),
            }

            if item in item_actions:
                await item_actions[item](inter, user_id)
            else:
                await inter.followup.send("This item is not recognized.")

        except Exception as e:
            # Consider logging instead of printing
            print(f"Error using item: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error processing your request: {e}")
            )

    @commands.slash_command(name="sell", description="Sell your belongings.")
    async def sell(
        self,
        inter: disnake.ApplicationCommandInteraction,
        item: str = commands.Param(
            choices=["Fish", "Meme Karma"], description="The item to sell."
        ),
        amount: int = commands.Param(description="The quantity of the item to sell."),
    ):
        await inter.response.defer()
        user_id = str(inter.author.id)

        try:
            if item == "Fish":
                coins_amount = 25  # Define the amount of coins earned per fish
                success = await self.db_handler.money_sell_fish(user_id, amount)
                if isinstance(success, bool):  # Check if success is a boolean
                    if success:
                        await inter.followup.send(
                            f"Successfully sold **{amount}** fish for **{amount * coins_amount}** <:coin:1270075840901812304>"
                        )
                else:
                    await inter.followup.send(f"You only have **{success}** Fish!")

            elif item == "Meme Karma":
                coins_amount = 2  # Define the amount of coins earned per karma
                success = await self.db_handler.money_sell_karma(user_id, amount)
                if isinstance(success, bool):  # Check if success is a boolean
                    if success:
                        await inter.followup.send(
                            f"Successfully traded **{amount}** Karma for **{amount * coins_amount}** <:coin:1270075840901812304>"
                        )
                else:
                    # This case handles when success is not a boolean but an integer (current karma)
                    await inter.followup.send(f"You only have **{success}** Karma!")

            else:
                await inter.followup.send(
                    "Invalid item selected. Please choose between Fish and Meme Karma."
                )

        except Exception as e:
            print(f"Error in sell command: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"Error processing sell command: {e}")
            )

    @commands.slash_command(
        name="postmeme",
        description="Use your laptop to post memes! There's a slight chance that your laptop breaks!",
    )
    async def postmeme(
        self,
        inter: disnake.ApplicationCommandInteraction,
        type: str = commands.Param(
            choices=["Epic Meme", "Prestigious Meme", "Intellectual Meme", "Kind Meme"],
            description="The type of meme you want to post.",
        ),
    ):
        user_id = inter.author.id
        await inter.response.defer()

        try:
            now = datetime.utcnow()

            # Check for cooldown
            if user_id in self.cooldowns and now < self.cooldowns[user_id]:
                time_remaining = (self.cooldowns[user_id] - now).total_seconds()
                await inter.followup.send(
                    f"You've already posted a meme recently. Post a new one again in **{int(time_remaining)}s**"
                )
                return

            # Generate random amount of karma
            amount = random.randint(0, 2500)

            # Add karma to user
            success, has_laptop = await self.db_handler.money_add_karma(user_id, amount)

            if not has_laptop:
                await inter.followup.send(
                    "You don't have a Laptop! Buy it from `/shop` first!"
                )
                return

            if not success:
                await inter.followup.send(
                    "There was an error adding karma. Please try again later."
                )
                return

            # Slight chance that the laptop breaks
            if random.random() < 0.1:  # 10% chance
                self.money_remove_item(user_id, "Laptop")
                await inter.followup.send(
                    "Oh no! Your laptop broke while posting the meme!"
                )

            # Update cooldown
            self.cooldowns[user_id] = now + timedelta(minutes=1)

            # Determine message based on karma amount
            if amount == 0:
                message = (
                    "Oops! Your meme didn't get any response. Better luck next time!"
                )
            elif amount <= 500:
                message = (
                    f"Hey! Your meme got a decent response! You got {amount} Karma!"
                )
            elif amount <= 900:
                message = f"Your meme is EXPLODING! You got {amount} Karma!"
            else:
                message = f"Wow! Your meme went viral! You got {amount} Karma!"

            await inter.followup.send(
                f"**TIP**: Use `/sell` to trade your karma for money!.\n{message}"
            )

        except Exception as e:
            print(f"Error in postmeme command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"An error occurred while posting your meme: {e}"
                )
            )

    @commands.slash_command(name="profile", description="View your Inventory")
    async def profile(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="The User to view their balance of.", default=None
        ),
    ):
        await inter.response.defer()
        if user is None:
            user = inter.author

        user_id = str(user.id)

        try:
            inventory_data, pocket, bank, karma = await self.db_handler.money_profile(
                user_id
            )

            networth = pocket + bank

            pocket_formatted = "{:,}".format(pocket)
            bank_formatted = "{:,}".format(bank)
            networth_formatted = "{:,}".format(networth)

            embed = disnake.Embed(
                title=f"{user.name}#{user.discriminator}'s Profile",
                description="",
                color=0xE67E22,
            )

            embed.add_field(
                name="Normal Stats",
                value=(
                    f"**Pocket:** {pocket_formatted}\n"
                    f"**Bank:** {bank_formatted}\n"
                    f"**Net Worth:** {networth_formatted}\n"
                    f"**Meme Karma:** {karma}"
                ),
                inline=False,
            )

            # Extract inventory values with defaults to 0
            cat = inventory_data.get("cat", 0)
            car = inventory_data.get("car", 0)
            minecraft = inventory_data.get("minecraft", 0)
            mansion = inventory_data.get("mansion", 0)
            fish = inventory_data.get("fish", 0)
            laptop = inventory_data.get("laptop", 0)

            fish_formatted = "{:,}".format(fish)

            # Add inventory items field to embed
            embed.add_field(
                name="Items",
                value=(
                    f"Cats: **{cat}**\n"
                    f"Cars: **{car}**\n"
                    f"Minecraft Copies: **{minecraft}**\n"
                    f"Mansions: **{mansion}**\n"
                    f"Fishes Caught: **{fish_formatted}**\n"
                    f"Laptops: **{laptop}**"
                ),
                inline=False,
            )

            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            embed.set_thumbnail(url=avatar_url)

            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error retrieving profile for user {user_id}: {e}")
            await inter.followup.send(
                "An error occurred while retrieving the profile. Please try again later."
            )

        except Exception as e:
            print(f"Error showing profile: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error showing profile: {e}")
            )


def setup(bot):
    bot.add_cog(economy(bot))
