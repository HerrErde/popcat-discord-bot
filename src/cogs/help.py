import config
import disnake
from disnake.ext import commands
from disnake.ui import Select, View

from helpers import errors


class help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Loaded Cog Help")

    @commands.slash_command(
        name="help",
        description="Get the list of commands",
    )
    async def help(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        try:
            embed = disnake.Embed(
                title="Pop Cat Bot Help",
                description="This is the command list for the pop cat bot.\nRemember that it is slash commands only!",
                color=disnake.Color.blue(),
            )
            embed.add_field(
                name="<a:POPCAT:1288559997944467590> | Fun",
                value="`Use The Menu`",
                inline=True,
            )
            embed.add_field(
                name="<a:geary:1269562283181211728> | Utility",
                value="`Use The Menu`",
                inline=True,
            )
            embed.add_field(
                name="<:money:1269562304517767221> | Economy",
                value="`Use The Menu`",
                inline=True,
            )
            embed.add_field(
                name=":tickets: | Tickets",
                value="`Use The Menu`",
                inline=True,
            )
            embed.add_field(
                name="<a:popcat_popcorn:1269562318971211817> | Image Generation",
                value="`Use The Menu`",
                inline=True,
            )
            embed.add_field(
                name="<a:gem:1269562295886020671> | Moderation",
                value="`Use The Menu`",
                inline=True,
            )
            embed.add_field(
                name=":eyes: | Searching",
                value="`Use The Menu`",
                inline=True,
            )
            if config.CHATBOT_ENABLE:
                embed.add_field(
                    name="<a:code:1269569111134834830> | Chatbot",
                    value="`Use The Menu`",
                    inline=True,
                )
            embed.add_field(
                name=":earth_asia: | Game",
                value="`Use The Menu`",
                inline=True,
            )
            embed.add_field(
                name="<a:tada:1269568942377140244> | Welcoming",
                value="`Use The Menu`",
                inline=True,
            )
            bot_avatar_url = (
                self.bot.user.avatar.url
                if self.bot.user.avatar
                else self.bot.user.default_avatar.url
            )
            embed.set_thumbnail(url=bot_avatar_url)
            embed.set_footer(
                text="Made By HerrErde.",
            )

            # select menu
            select = Select(
                placeholder="Nothing selected",
                options=[
                    disnake.SelectOption(
                        label="Source Code",
                        emoji="a:code:1269569111134834830",
                        value="SourceCode",
                    ),
                    disnake.SelectOption(
                        label="Fun",
                        emoji="a:POPCAT:1288559997944467590",
                        value="Fun",
                    ),
                    disnake.SelectOption(
                        label="Utility",
                        emoji="a:geary:1269562283181211728",
                        value="Utility",
                    ),
                    disnake.SelectOption(
                        label="Economy",
                        emoji="a:money:1269562304517767221",
                        value="Economy",
                    ),
                    disnake.SelectOption(
                        label="Geography Game",
                        emoji="🌎",
                        value="Geography Game",
                    ),
                    disnake.SelectOption(
                        label="Tickets",
                        emoji="🎟️",
                        value="Tickets",
                    ),
                    disnake.SelectOption(
                        label="Image Generation",
                        emoji="a:popcat_popcorn:1269562318971211817",
                        value="Generation",
                    ),
                    disnake.SelectOption(
                        label="Moderation",
                        emoji="a:gem:1269562295886020671",
                        value="Moderation",
                    ),
                    disnake.SelectOption(
                        label="Searching",
                        emoji="👀",
                        value="Searching",
                    ),
                    disnake.SelectOption(
                        label="Welcoming",
                        emoji="a:tada:1269568942377140244",
                        value="Welcoming",
                    ),
                    disnake.SelectOption(
                        label="Chatbot",
                        emoji="a:code:1269569111134834830",
                        value="Chatbot",
                    ),
                ],
            )

            vote_link = "`/Vote Link`, " if config.VOTING_ENABLE else ""
            vote_reward = ", `/vote rewards`" if config.VOTING_ENABLE else ""

            async def select_callback(interaction: disnake.MessageInteraction):
                selected_category = interaction.data["values"][0]
                category_list = {
                    "SourceCode": None,
                    "Fun": disnake.Embed(
                        title=":POPDOG: | Fun",
                        description="`Avatar`, `8ball`, `Ascii`, `Cat`, `Colorify`, `Ship`, `/Text Emojify | Lolcat | Spoiler | Clap | Reverse | Flip | Zalgo | Roman-Numerals`, `Pong`, `Colorinfo`, `Obama`, `Today`, `Choose`, `Car`, `Google-Autocomplete`, `Periodic-Table`, `Trivia`, `Country`, `ChemSpeller`, `Dino`, `WorldClock`, `Distance`",
                        colour=disnake.Color.orange(),
                    ),
                    "Utility": disnake.Embed(
                        title="<a:geary:1269562283181211728> | Utility Commands",
                        description=f"`Serverinfo`, `Poll`, `/Bio Set | View`, `Embed`, `Help`, `Info`, `Poll`, `Roleinfo`, `Top-invites`, `Userinfo`, `/Todo Add | Delete | List`, `suggest`, `Firstmessage`, `Report`, `/AFK Set`, {vote_link}`/Set-updates`, `qrcode`, `/Custom-Commands` `Create` | `Delete` | `List`, `/Changes`, `Enlarge`, `/Custom-Command`",
                        colour=disnake.Color.blurple(),
                    ),
                    "Economy": disnake.Embed(
                        title="<:money:1269562304517767221> | Economy Commands",
                        description=f"`/beg`, `/bal`, `/work`, `/daily`, `/slots`, `/give`, `/deposit`, `/withdraw`, `/shop`, `/buy`, `/leaderboard bank | pocket`, `/use`, `/sell`, `/postmeme`{vote_reward}",
                        colour=disnake.Color.orange(),
                    ),
                    "Geography Game": disnake.Embed(
                        title=":earth_asia: | Geography Game",
                        description="`/Guess-The-Country` `Start` | `Giveup` | `LeaderBoard` | `Guess` | `History`",
                        color=disnake.Color.blue(),
                    ),
                    "Tickets": disnake.Embed(
                        title=":tickets: | Ticket Commands",
                        description="`/Ticket-setup` Rol`e | `Category` | `Info` | `Panel`, `/ticket`",
                        colour=disnake.Color.dark_theme(),
                    ),
                    "Image Generation": disnake.Embed(
                        title="<a:popcat_popcorn:1269562318971211817> | :Image Generation Commands",
                        description="`Biden`, `Gun`, `/Image` `Cmm` | `Drip` | `Stonks` | `Invert` | `Triggered` | `Opinion` | `WhoWouldWin` | `Communism` | `Wide` | `Distort` | `Pooh` | `Fuse` | `Quote`",
                        colour=disnake.Color.orange(),
                    ),
                    "Moderation": disnake.Embed(
                        title="<a:gem:1269562295886020671> | Moderation Commands",
                        description="`Warn`, `Warns`, `Removewarn`, `[/Suggestions Set | Disable]`",
                        colour=disnake.Color.blue(),
                    ),
                    "Searching": disnake.Embed(
                        title=":eyes: | Search Commands",
                        description="`Reddit`, `NPM`, `GitHub`, `Periodic-Table`, `Country`",
                        colour=0xFFCC99,
                    ),
                    "Welcoming": disnake.Embed(
                        title="<a:tada:1269568942377140244> | Welcoming Commands",
                        description="`/Welcome-setup` `Info` | `Channel` | `Message` | `Test` | `Disable`",
                        colour=disnake.Color.purple(),
                    ),
                    "Chatbot": disnake.Embed(
                        title="<a:code:1269569111134834830> | Chatbot Commands",
                        description="`/Chatbot` `Channel` | `Disable`",
                        colour=disnake.Color.blue(),
                    ),
                }

                if selected_category in category_list:
                    message = category_list[selected_category]

                    if selected_category == "SourceCode":
                        button = disnake.ui.Button(
                            label="GitHub Repository",
                            url="https://github.com/herrerde/popcat-discord-bot",
                        )
                        view = View()
                        view.add_item(button)
                        await interaction.response.send_message(
                            content="Here You Go!",
                            view=view,
                            ephemeral=True,
                        )
                    else:
                        await interaction.response.send_message(
                            embed=message, ephemeral=True
                        )
                else:
                    await interaction.response.send_message(
                        content="Invalid selection.", ephemeral=True
                    )

            select.callback = select_callback

            view = View()
            view.add_item(select)

            await inter.response.send_message(embed=embed, view=view)

        except Exception as e:
            print(f"Error sending help message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error sending help command: {e}", ephemeral=True
                )
            )


def setup(bot):
    bot.add_cog(help(bot))
