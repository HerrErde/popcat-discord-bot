import disnake
from disnake.ext import commands

import config
from db import DBHandler
from helpers import errors


class todo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Todo")
        await self.db_handler.initialize()

    @commands.slash_command(name="todo")
    async def todo(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @todo.sub_command(name="add", description="Create a new todo!")
    async def todo_add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(description="The title of your todo."),
        description: str = commands.Param(description="The description of your todo."),
    ):
        try:
            user_id = str(inter.user.id)

            # Add the new todo
            success = await self.db_handler.add_todo(user_id, title, description)

            # get the updated list of todos
            todo_list = await self.db_handler.list_todo(user_id)

            embed_color = disnake.Color.blue() if success else disnake.Color.fuchsia()

            embed = disnake.Embed(title="Your TODO List", color=embed_color)

            if todo_list:
                for idx, todo in enumerate(todo_list):
                    embed.add_field(
                        # name=f"{idx + 1}. {todo['title']}", # for numberd list
                        name=f"{todo['title']}",
                        value=todo["description"],
                        inline=True,
                    )
            else:
                embed.add_field(
                    name="No todos found",
                    value="Your todo list is empty.",
                    inline=False,
                )

            embed.set_footer(text=f"View your todos online on {config.TODO_WEB_URL} !")

        except Exception as e:
            print(f"An error occurred while adding a todo: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Failed to add todo: {e}")
            )
            return

        await inter.response.send_message(embed=embed)

    @todo.sub_command(name="delete", description="Delete a todo!")
    async def todo_delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(description="The Title of your todo"),
    ):
        try:
            user_id = str(inter.user.id)

            await self.db_handler.remove_todo(user_id, title)

            # get the updated list of todos
            todo_list = await self.db_handler.list_todo(user_id)

            embed_color = disnake.Color.blue() if todo_list else disnake.Color.fuchsia()

            embed = disnake.Embed(title="Your TODO List", color=embed_color)

            if todo_list:
                for idx, todo in enumerate(todo_list):
                    embed.add_field(
                        name=f"{idx + 1}. {todo['title']}",
                        value=todo["description"],
                        inline=True,
                    )
            else:
                embed.add_field(
                    name="No todos found",
                    value="Your todo list is empty.",
                    inline=False,
                )

            embed.set_footer(text=f"View your todos online on {config.TODO_WEB_URL} !")

        except Exception as e:
            print(f"An error occurred while deleting todo item: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Failed to delete todo: {e}")
            )
            return

        await inter.response.send_message(embed=embed)

    @todo.sub_command(name="list", description="Shows all your todos.")
    async def todo_list(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        try:
            user_id = str(inter.user.id)

            # get list of todos
            todo_list = await self.db_handler.list_todo(user_id)

            embed_color = disnake.Color.blue() if todo_list else disnake.Color.fuchsia()

            embed = disnake.Embed(title="Your TODO List", color=embed_color)

            if todo_list:
                for idx, todo in enumerate(todo_list):
                    embed.add_field(
                        name=f"{idx + 1}. {todo['title']}",
                        value=todo["description"],
                        inline=True,
                    )
            else:
                embed.add_field(
                    name="No todos found",
                    value="Your todo list is empty.",
                    inline=False,
                )

            embed.set_footer(text=f"View your todos online on {config.TODO_WEB_URL} !")

        except Exception as e:
            print(f"An error occurred while getting todo: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Failed to get todo list: {e}")
            )
            return

        await inter.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(todo(bot))
