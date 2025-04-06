import config
import disnake
from disnake.ext import commands

from db import DBHandler
from helpers import errors
from module import Stocks


class stocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Stocks")
        await self.db_handler.initialize()

    async def autocomp_stock(
        inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        stocks_list = await Stocks.stocks_list()

        filtered_stocks = [
            stock for stock in stocks_list if user_input.lower() in stock.lower()
        ]

        return filtered_stocks[:25]

    @commands.slash_command(
        name="stocks", description="Buy, sell and check stock prices."
    )
    async def stocks(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @stocks.sub_command(name="buy", description="Buy a Stock with pop coins.")
    async def buy(
        self,
        inter: disnake.ApplicationCommandInteraction,
        stock: str = commands.Param(
            autocomplete=autocomp_stock,
            description="The Stock Symbol To Buy",
        ),
        amount: int = commands.Param(
            description="The amount of Pop Coins to invest.",
        ),
    ):
        await inter.response.defer()

        if stock not in Stocks.stocks_list:
            await inter.followup.send(
                embed=errors.create_error_embed(f"Invalid item selected: {e}")
            )
            return

        user_id = str(inter.author.id)

        try:
            symbol = stock.split(" - ")[0].lower()

            shares, loss, loss_perc, price = await Stocks.stock_info(symbol, amount)
            if config.DEBUG:
                print(
                    f"Shares: {shares}, Loss: {loss}, Loss %: {loss_perc}, Price/share $: {price}"
                )

            success, item_added = await self.db_handler.stocks_buy(
                user_id, symbol, shares, amount, price
            )
            if success:
                if item_added:
                    message = f"🚀🚀 Successfully bought `{shares:.3f}` shares of **{symbol.upper()}** for `{amount}` <a:coin:1270075840901812304>."
                else:
                    message = "You don't have enough Pop Coins in your bank account to buy this stock."
            else:
                message = "Failed to process the transaction. Please try again later."

            await inter.followup.send(message)

        except Exception as e:
            print(f"Error processing buy command: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"An error occurred: {e}")
            )

    @stocks.sub_command(
        name="sell",
        description="Sell a stock for pop coins.",
    )
    async def sell(
        self,
        inter: disnake.ApplicationCommandInteraction,
        stock: str = commands.Param(
            autocomplete=autocomp_stock,
            description="The Stock Symbol To Sell",
        ),
        amount: int = commands.Param(
            description="The value of stock to sell.",
        ),
    ):

        await inter.response.defer()

        if stock not in Stocks.stocks_list:
            await inter.followup.send(
                embed=errors.create_error_embed(f"Invalid item selected: {stock}")
            )
            return

        user_id = str(inter.author.id)

        try:
            symbol = stock.split(" - ")[0].lower()

            shares, loss, loss_perc, price = await Stocks.stock_info(symbol, amount)
            print(
                f"Shares: {shares}, Loss: {loss}, Loss %: {loss_perc}, Price/share $: {price}"
            )
            if shares is None:
                message = "Failed to fetch the stock price. Please try again later."

            success, item_added = await self.db_handler.stocks_sell(
                user_id, symbol, shares, amount, price
            )

            if success:
                if item_added:
                    message = f"💰 Successfully sold `{shares}` shares of **{symbol.upper()}** for `{amount}` :PopCoin:. Loss: ${loss:.2f} ({loss_perc:.2f}%)"
            else:
                message = "You don't own enough of this stock to sell."

            await inter.followup.send(message)

        except Exception as e:
            print(f"Error processing buy command: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"An error occurred: {e}")
            )

    @stocks.sub_command(
        name="portfolio",
        description="Check your current holdings and their values.",
    )
    async def portfolio(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="View this User's portfolio.", default=None
        ),
    ):
        await inter.response.defer()

        if user is None:
            user = inter.author

        user_id = str(user.id)

        try:
            # Fetch all necessary stock data for the user's portfolio
            user_data = await self.db_handler.stocks_portfolio(user_id)

            # Ensure portfolio data is available
            if not user_data or not isinstance(user_data, dict):
                return await inter.followup.send(
                    content="Your portfolio is empty. Buy some stocks to start investing!"
                )
                # return await inter.followup.send(embed=disnake.Embed(title=f"{user.name}'s Stock Portfolio",description="You don't own any stocks yet!",color=0x57F288))

            # Prepare portfolio data
            total_portfolio_value = 0
            total_profit_loss = 0
            portfolio_details = []

            # Loop through each stock in the portfolio
            for symbol, data in user_data.items():
                transactions = data["transactions"]
                total_shares = 0
                total_cost = 0
                total_value = 0
                total_profit_loss_for_stock = 0

                # Process each transaction for the current stock symbol
                for txn in transactions:
                    if txn["action"] == "buy":
                        total_shares += txn["shares"]
                        total_cost += txn["shares"] * txn["price"]
                    elif txn["action"] == "sell":
                        total_shares -= txn["shares"]
                        total_cost -= txn["shares"] * txn["price"]

                # Await the current stock price asynchronously
                # Await the async function
                current_price = await Stocks.stock_price(symbol)
                total_value = total_shares * current_price
                total_profit_loss_for_stock = total_value - total_cost

                # Add stock value to the total portfolio value and profit/loss
                total_portfolio_value += total_value
                total_profit_loss += total_profit_loss_for_stock

                # Build portfolio details for each stock
                profit_perc = (
                    (total_profit_loss_for_stock / total_cost) * 100
                    if total_cost > 0
                    else 0
                )
                portfolio_details.append(
                    f"**{symbol.upper()}**: {total_shares:.3f} shares, Current Price: ${current_price:.2f}, "
                    f"Total Value: ${total_value:,.2f}, "
                    f"{'Profit' if total_profit_loss_for_stock >= 0 else 'Loss'}: ${total_profit_loss_for_stock:,.2f} ({profit_perc:+.2f}%)"
                )

            # Calculate the total loss percentage for the portfolio
            total_loss_perc = (
                (total_profit_loss / total_portfolio_value) * 100
                if total_portfolio_value > 0
                else 0
            )

            # Build the embed message
            embed = disnake.Embed(
                title=f"🚀 {user.name}'s Stock Portfolio",
                description="\n".join(portfolio_details),
                color=0x57F288,
            )

            embed.add_field(
                name="Total Portfolio Value",
                value=f"${total_portfolio_value:,.2f}",
                inline=True,
            )
            embed.add_field(
                name="Total Profit/Loss",
                value=f"${total_profit_loss:,.2f} ({total_loss_perc:+.2f}%)",
                inline=True,
            )
            embed.set_footer(text="Keep building your portfolio! 🚀")

            # Send the embed as the response
            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error displaying portfolio: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"An error occurred: {e}")
            )

    @stocks.sub_command(
        name="price",
        description="Check the current stock price.",
    )
    async def price(
        self,
        inter: disnake.ApplicationCommandInteraction,
        stock: str = commands.Param(
            autocomplete=autocomp_stock,
            description="The Stock Symbol to Check.",
        ),
    ):

        await inter.response.defer()
        try:
            stock = stock.split(" - ")[0].lower()
            (
                success,
                symbol,
                current_price,
                previous_close,
                open_price,
                high_price,
                low_price,
                daily_change_dollar,
                daily_change_percent,
            ) = await Stocks.stocks_data(stock)

            if success:
                embed = disnake.Embed(
                    title=f"Current Stock Price for ${symbol.lower()}",
                    description="",
                    color=0x57F288,
                )
                embed.add_field(
                    name=f"Current Price",
                    value=f"${current_price:.2f}",
                    inline=True,
                )
                embed.add_field(
                    name=f"Previous Close",
                    value=f"${previous_close:.2f}",
                    inline=True,
                )
                embed.add_field(
                    name=f"Open",
                    value=f"${open_price:.2f}",
                    inline=True,
                )
                embed.add_field(
                    name=f"High",
                    value=f"${high_price:.2f}",
                    inline=True,
                )
                embed.add_field(
                    name=f"Low",
                    value=f"${low_price:.2f}",
                    inline=True,
                )
                daily_change_dollar = f"{daily_change_dollar:+.2f}"
                daily_change_percent = f"{daily_change_percent:+.2f}%"

                embed.add_field(
                    name="Today's Change",
                    value=f"{daily_change_dollar} ({daily_change_percent})",
                    inline=True,
                )
            else:
                embed = disnake.Embed(
                    title=f"Stock symbol `${symbol.lower()}` does not exsist",
                    description="",
                    color=disnake.Color.red(),
                )

            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error processing price command: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(f"An error occurred: {e}")
            )

    @stocks.sub_command(
        name="leaderboard",
        description="Check the top performers in the stock competition.",
    )
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

        try:
            # get leaderboard data
            leaderboard_data = await self.db_handler.stocks_leaderboard()

            if not leaderboard_data:
                await inter.followup.send("No users found in the leaderboard.")
                return

            # Fetch all members of the guild and map their display names
            all_members = await inter.guild.fetch_members(limit=None).flatten()
            user_names = {
                str(
                    member.id
                ): f"{member.name}{'' if member.discriminator == '0' else f'#{member.discriminator}'}"
                for member in all_members
            }

            embed = disnake.Embed(
                title="Stock Portfolio Leaderboard",
                description="Top users with the highest current stock portfolio value:",
                color=0x57F288,
            )

            # Loop through sorted leaderboard and add to the embed
            for rank, (user_id, total_value) in enumerate(
                leaderboard_data.items(), start=1
            ):
                username = user_names.get(user_id, f"Unknown User ({user_id})")
                embed.add_field(
                    name=f"#{rank} - {username}",
                    value=f"${total_value:,.2f}",
                    inline=False,
                )

            # Send the embed
            await inter.followup.send(embed=embed)

        except Exception as e:
            print(f"Error creating stocks leaderboard: {e}")
            await inter.followup.send(
                embed=errors.create_error_embed(
                    f"An error occurred while generating the leaderboard: {e}"
                )
            )


def setup(bot):
    bot.add_cog(stocks(bot))
