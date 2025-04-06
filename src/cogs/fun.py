import html
import random
from functools import partial

import aiohttp
import disnake
import pyfiglet
from disnake.ext import commands
from zalgo_text import zalgo

from helpers import errors
from module.text import translate


class fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Fun")

    @commands.slash_command(
        name="avatar",
        description="Get a user's avatar",
    )
    async def avatar(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(description="The User to get the avatr of"),
    ):
        try:
            avatar_url_base = (
                user.avatar.url if user.avatar else user.default_avatar.url
            )
            avatar_url_jpg = f"{avatar_url_base[:-14]}.jpg?size=1024"
            avatar_url_webp = f"{avatar_url_base[:-14]}.webp?size=1024"
            avatar_url_gif = f"{avatar_url_base[:-14]}.gif?size=1024"

            embed = disnake.Embed(title=f"{user.display_name}'s Avatar", color=0xFFCC99)
            embed.add_field(
                name="",
                value=f"[PNG]({avatar_url_base}) | [JPG]({avatar_url_jpg}) | [WEBP]({avatar_url_webp}) | [GIF]({avatar_url_gif})",
                inline=True,
            )
            embed.set_image(
                url=user.avatar.url if user.avatar else user.default_avatar.url
            )

            await inter.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error sending user avatar command: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error sending user avatar command: {e}"
                )
            )

    @commands.slash_command(name="8ball", description="Ask the magic 8ball a question!")
    async def eightball(
        self,
        inter: disnake.ApplicationCommandInteraction,
        question: str = commands.Param(description="The question"),
    ):
        try:
            responses = [
                "It is certain.",
                "It is decidedly so.",
                "Without a doubt.",
                "Yes - definitely.",
                "You may rely on it.",
                "As I see it, yes.",
                "Most likely.",
                "Outlook good.",
                "Yes.",
                "Signs point to yes.",
                "Reply hazy, try again.",
                "Ask again later.",
                "Better not tell you now.",
                "Cannot predict now.",
                "Concentrate and ask again.",
                "Don't count on it.",
                "My reply is no.",
                "My sources say no.",
                "Outlook not so good.",
                "Very doubtful.",
                "When you grow a braincell, yes",
                "THAT'S A SOLID ****NO****",
                "idk UwU ask pop cat",
                "Shut up you rat!",
                "Just shut up beech",
                "As I see it",
                "Nah that sucks tbh",
                "Yes - definitely",
                "sure, why not",
                "Not sure",
                "Maybe",
                "Ask again sometime later.",
                "No",
            ]
            embed = disnake.Embed(
                title=f"Pop Cat's 8Ball :8ball:",
                color=disnake.Color.random(),
            )
            embed.add_field(
                name=f"**Your Question**:", value=f"{question}", inline=False
            )
            embed.add_field(
                name=f"**8Ball**:", value=f"{random.choice(responses)}", inline=False
            )

            await inter.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error sending 8ball message: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error sending 8 Ball command: {e}")
            )

    @commands.slash_command()
    async def text(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @text.sub_command(
        name="roman-numerals", description="Turn a number into Roman numerals."
    )
    async def roman_numerals(
        self,
        inter: disnake.ApplicationCommandInteraction,
        number: int = commands.Param(description="The Number"),
    ):
        try:

            def int_to_roman(num):
                val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
                syb = [
                    "M",
                    "CM",
                    "D",
                    "CD",
                    "C",
                    "XC",
                    "L",
                    "XL",
                    "X",
                    "IX",
                    "V",
                    "IV",
                    "I",
                ]
                roman_num = ""
                i = 0
                while num > 0:
                    for _ in range(num // val[i]):
                        roman_num += syb[i]
                        num -= val[i]
                    i += 1
                return roman_num

            roman_numeral = int_to_roman(number)
            output = (
                f"**Original Number**: {number} \n**Roman Numeral**: {roman_numeral}"
            )

            await inter.response.send_message(output)
        except Exception as e:
            print(f"Error sending Roman numerals message: {e}")

    @text.sub_command(name="reverse", description="Reverse the text")
    async def reverse(self, inter: disnake.ApplicationCommandInteraction, text: str):
        try:
            styled_text = text[::-1]
            await inter.response.send_message(styled_text)
        except Exception as e:
            await inter.response.send_message(f"Error sending reversed text: {e}")

    @text.sub_command(name="flip", description="Flip the text upsidedown")
    async def flip(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The text"),
    ):
        try:
            UPSIDE_DOWN_MAP = {
                ",": "\u02bb",
                "!": "\u00a1",
                "?": "\u00bf",
                ".": "\u0387",
                "'": "\u02cc",
                '"': "\u02cc\u02cc",
                "*": "\u2093",
                "&": "\u214b",
                "1": "\u0196",
                "2": "\u0547",
                "3": "\u0190",
                "4": "h",
                "5": "\ud801\udc55",
                "6": "9",
                "7": "L",
                "9": "6",
                "A": "\u2c6f",
                "a": "\u0250",
                "B": "\ua4ed",
                "b": "q",
                "C": "\ua4db",
                "c": "\u0254",
                "D": "\ua4f7",
                "d": "p",
                "E": "\u018e",
                "e": "\u01dd",
                "F": "\ua4de",
                "f": "\u025f",
                "G": "\ua4e8",
                "g": "\u0253",
                "h": "\u0265",
                "i": "\u1d09",
                "J": "\u017f",
                "j": "\ua4e9",
                "K": "\ua4d8",
                "k": "\u029e",
                "L": "\ua4f6",
                "l": "\u0285",
                "M": "W",
                "m": "\u026f",
                "n": "u",
                "P": "\ua4d2",
                "p": "d",
                "Q": "\u1ff8",
                "q": "b",
                "R": "\ua4e4",
                "r": "\u0279",
                "T": "\ua4d5",
                "t": "\u0287",
                "U": "\ua4f5",
                "u": "n",
                "V": "\ua4e5",
                "v": "\u028c",
                "W": "M",
                "w": "\u028d",
                "Y": "\u2144",
                "y": "\u028e",
            }

            flipped_text = "".join(UPSIDE_DOWN_MAP.get(char, char) for char in text)
            styled_text = flipped_text[::-1]

            await inter.response.send_message(styled_text)
        except Exception as e:
            print(f"Error sending flip message: {e}")

    @text.sub_command(name="space", description="Space out the text")
    async def space(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The text"),
    ):
        try:
            styled_text = " ".join(text)

            await inter.response.send_message(styled_text)
        except Exception as e:
            print(f"Error sending space message: {e}")

    @text.sub_command(name="clap", description="Clap")
    async def clap(self, inter: disnake.ApplicationCommandInteraction, text: str):
        try:
            styled_text = ":clap:".join(text)
            await inter.response.send_message(styled_text)
        except Exception as e:
            print(f"Error sending clap message: {e}")

    @text.sub_command(name="spoiler", description="Turn text into a spoiler")
    async def spoiler(self, inter: disnake.ApplicationCommandInteraction, text: str):
        try:

            styled_text = f"||{text}||"

            await inter.response.send_message(styled_text)
        except Exception as e:
            print(f"Error sending spoiler message: {e}")

    @text.sub_command(name="zalgo", description="Turn text into zalgo")
    async def spoiler(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The text"),
    ):
        try:
            styled_text = zalgo.zalgo().zalgofy(text)

            await inter.response.send_message(styled_text)
        except Exception as e:
            print(f"Error sending spoiler message: {e}")  #

    @text.sub_command(name="emojify", description="Turn text into emojis")
    async def emojify(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The text"),
    ):
        try:
            emoji_map = {
                "0": ":zero:",
                "1": ":one:",
                "2": ":two:",
                "3": ":three:",
                "4": ":four:",
                "5": ":five:",
                "6": ":six:",
                "7": ":seven:",
                "8": ":eight:",
                "9": ":nine:",
                " ": " ",
                ".": ":radio_button:",
                "!": ":grey_exclamation:",
                "?": ":grey_question:",
                "ä": ":regional_indicator_a::regional_indicator_e:",
                "ö": ":regional_indicator_o::regional_indicator_e:",
                "ü": ":regional_indicator_u::regional_indicator_e:",
                "ß": ":regional_indicator_s::regional_indicator_s:",
            }

            result = ""
            for char in text.lower():
                if char in emoji_map:
                    result += emoji_map[char]
                elif char.isalpha():
                    result += f":regional_indicator_{char}:"
                else:
                    result += char

            await inter.response.send_message(result)
        except Exception as e:
            print(f"Error sending emojified message: {e}")

    @text.sub_command(
        name="lolcat",
        description="Turn text into lolcat language",
    )
    async def lolcat(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The text"),
    ):
        try:
            response = translate.lolcat(text)
            output = response.upper()
            await inter.response.send_message(content=output)
        except Exception as e:
            await inter.response.send_message(content=f"Error: {e}")

    @commands.slash_command(name="trivia", description="Play a Game of Trivia!")
    async def trivia(
        self,
        inter: disnake.ApplicationCommandInteraction,
        difficulty: str = commands.Param(
            choices=[
                "easy",
                "medium",
                "hard",
            ],
            description="The difficulty of the trivia game",
        ),
        category: str = commands.Param(
            choices=[
                "General Knowledge",
                "Entertainment: Books",
                "Entertainment: Film",
                "Entertainment: Music",
                "Entertainment: Musicals & Theatres",
                "Entertainment: Television",
                "Entertainment: Video Games",
                "Entertainment: Board Games",
                "Science & Nature",
                "Science: Computers",
                "Science: Mathematics",
                "Mythology",
                "Sports",
                "Geography",
                "History",
                "Politics",
                "Art",
                "Celebrities",
                "Animals",
                "Vehicles",
                "Entertainment: Comics",
                "Science: Gadgets",
                "Entertainment: Japanese Anime & Manga",
                "Entertainment: Cartoon & Animations",
            ],
            default=None,
            description="The category of the trivia questions.",
        ),
        type: str = commands.Param(
            choices=["Options", "Text"],
            default="Options",
            description="The output of the Question format",
        ),
    ):
        try:
            category_map = {
                "General Knowledge": 9,
                "Entertainment: Books": 10,
                "Entertainment: Film": 11,
                "Entertainment: Music": 12,
                "Entertainment: Musicals & Theatres": 13,
                "Entertainment: Television": 14,
                "Entertainment: Video Games": 15,
                "Entertainment: Board Games": 16,
                "Science & Nature": 17,
                "Science: Computers": 18,
                "Science: Mathematics": 19,
                "Mythology": 20,
                "Sports": 21,
                "Geography": 22,
                "History": 23,
                "Politics": 24,
                "Art": 25,
                "Celebrities": 26,
                "Animals": 27,
                "Vehicles": 28,
                "Entertainment: Comics": 29,
                "Science: Gadgets": 30,
                "Entertainment: Japanese Anime & Manga": 31,
                "Entertainment: Cartoon & Animations": 32,
            }

            category_value = category_map.get(category) if category else None
            category_param = f"&category={category_value}" if category_value else ""

            url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&type=multiple{category_param}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

                    if data["response_code"] != 0:
                        await inter.response.send_message(
                            "Error fetching trivia question.", ephemeral=True
                        )
                        return

                    question_data = data["results"][0]
                    # Decode HTML entities in the question and answers
                    question = html.unescape(question_data["question"])
                    correct_answer = html.unescape(question_data["correct_answer"])
                    incorrect_answers = [
                        html.unescape(answer)
                        for answer in question_data["incorrect_answers"]
                    ]
                    question_category = html.unescape(question_data["category"])

                    if type == "Options":
                        # Combine all answers and shuffle them
                        all_answers = incorrect_answers + [correct_answer]
                        random.shuffle(all_answers)

                        # Convert answer options to A-D format
                        options = ["A", "B", "C", "D"]
                        answers_with_options = [
                            f"{options[i]} - {answer}"
                            for i, answer in enumerate(all_answers)
                        ]

                        embed = disnake.Embed(
                            title=question,
                            description="\n".join(answers_with_options),
                        )
                        embed.set_footer(
                            text=f"Category - {question_category}, Difficulty - {difficulty.capitalize()}"
                        )

                        view = disnake.ui.View()

                        async def button_callback(
                            interaction: disnake.MessageInteraction, correct_answer: str
                        ):
                            if interaction.component.label.endswith(correct_answer):
                                await interaction.response.edit_message(
                                    f":heavy_check_mark: You Got It Correct! The answer is {correct_answer}."
                                )
                            else:
                                await interaction.response.edit_message(
                                    f":x: You Got It Wrong! The correct answer is {correct_answer}."
                                )
                            for item in view.children:
                                item.disabled = True
                            await interaction.edit_original_message(
                                embed=None, view=None
                            )

                        for i, answer in enumerate(all_answers):
                            button = disnake.ui.Button(
                                label=options[i], style=disnake.ButtonStyle.primary
                            )
                            button.callback = partial(
                                button_callback, correct_answer=correct_answer
                            )
                            view.add_item(button)

                        await inter.response.send_message(
                            embed=embed, view=view, ephemeral=True
                        )

                    else:
                        # Combine all answers and shuffle them
                        all_answers = incorrect_answers + [correct_answer]
                        random.shuffle(all_answers)

                        embed = disnake.Embed(
                            title=question,
                            description="",
                        )
                        embed.set_footer(
                            text=f"Category - {question_category}, Difficulty - {difficulty.capitalize()}"
                        )

                        view = disnake.ui.View()

                        for answer in all_answers:
                            button = disnake.ui.Button(
                                label=answer, style=disnake.ButtonStyle.primary
                            )
                            view.add_item(button)

                        await inter.response.send_message(
                            embed=embed, view=view, ephemeral=True
                        )

        except Exception as e:
            print(f"Error trivia: {e}")

    @commands.slash_command(name="ascii", description="Turn text into ascii art")
    async def ascii(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(description="The text"),
    ):
        try:
            ascii_art = pyfiglet.figlet_format(text)

            # Send the ASCII art as a message
            await inter.response.send_message(f"```{ascii_art}```")
        except Exception as e:
            print(f"Error sending ASCII art message: {e}")


def setup(bot):
    bot.add_cog(fun(bot))
