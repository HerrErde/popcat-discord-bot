from datetime import datetime
from io import BytesIO

import disnake
from disnake.ext import commands

from module import chemspell


class Text(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Text")

    @commands.slash_command(
        name="chemspeller",
        description="Find elements from a word.",
    )
    async def chemspeller(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="Text to convert"),
    ):

        await inter.response.defer()
        try:
            if len(text) < 35:
                output_bytes, amount, spelled_word, element_list = chemspell.spell(text)
                if output_bytes:
                    embed = disnake.Embed(
                        title=f"Text Conversion Finished! [{amount}] Combinations Found",
                        description=f"{text} => {spelled_word} (`{', '.join(element_list)}`)",
                        color=disnake.Color.default(),
                    )
                    embed.set_footer(
                        text=f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    )
                    file = disnake.File(
                        BytesIO(output_bytes), filename="chemspeller.png"
                    )
                    embed.set_image(url="attachment://chemspeller.png")
                    await inter.send(file=file, embed=embed)
                else:
                    await inter.followup.send(
                        content="Cannot spell this word with element symbols"
                    )
            else:
                await inter.followup.send(content="Max Character Limit: **35**")
        except Exception as e:
            await inter.followup.send(content=f"Error: {e}")


def setup(bot):
    bot.add_cog(Text(bot))
