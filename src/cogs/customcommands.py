import config
import disnake
from disnake.ext import commands

from db import DBHandler


class customcommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Custom Commands")
        await self.db_handler.initialize()

    async def autocomp_commands(
        inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        try:
            guild_id = str(inter.guild.id)
            commands_list = await DBHandler().list_customcommands(guild_id)
            if config.DEBUG:
                print(f"Attempting to retrieve custom commands for guild {guild_id}...")

            # Filter and limit the list to 25 items
            filtered_commands = [
                command  # command is the command trigger (key)
                for command in commands_list
                if user_input.lower() in command.lower()
            ]

            if config.DEBUG:
                print(
                    f"Filtered commands based on user input '{user_input}': {filtered_commands[:25]}"
                )
            return filtered_commands[:25]

        except Exception as e:
            print(f"Error in autocomp_commands: {e}")
            return []

    @commands.slash_command(name="custom-command", description="Use a custom command.")
    async def custom_command(
        self,
        inter: disnake.ApplicationCommandInteraction,
        command: str = commands.Param(
            description="The Command Name", autocomplete=autocomp_commands
        ),
    ):
        await inter.response.defer()
        try:

            guild_id = str(inter.guild.id)
            response = await self.db_handler.get_customcommand(guild_id, command)

            if response:
                await inter.followup.send(content=response)
            else:
                await inter.followup.send(content="Custom command not found.")

        except Exception as e:
            print(f"Error retrieving custom command: {e}")
            if not inter.response.is_done():
                await inter.followup.send(content="Error retrieving custom command")

    @commands.slash_command(name="custom-commands")
    @commands.has_permissions(administrator=True)
    async def custom_commands(
        self, inter: disnake.ApplicationCommandInteraction, *args
    ):
        pass

    @custom_commands.sub_command(
        name="create", description="Create a custom command for the server."
    )
    async def create(
        self,
        inter: disnake.ApplicationCommandInteraction,
        command: str = commands.Param(description="The Command trigger."),
        response: str = commands.Param(description="The response to the command"),
    ):

        await inter.response.defer()
        try:

            guild_id = str(inter.guild.id)

            # Check if the command already exists
            command_exists = await self.db_handler.add_customcommand(
                guild_id, command, response
            )

            if command_exists:
                await inter.followup.send(
                    f"A command with that trigger already exists!"
                )
            else:
                await inter.followup.send(
                    f"Custom command `{command}` created successfully. Usage example: >{command}"
                )

        except Exception as e:
            print(f"Error creating command: {e}")
            if not inter.response.is_done():
                await inter.followup.send("Error creating command.")

    @custom_commands.sub_command(
        name="delete", description="Delete a custom command for the server."
    )
    @commands.has_permissions(administrator=True)
    async def delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        command: str = commands.Param(
            description="The Trigger of the Command to delete"
        ),
    ):

        await inter.response.defer()
        try:

            guild_id = str(inter.guild.id)

            if self.db_handler.remove_customcommand(guild_id, command):
                await inter.followup.send(
                    f"Custom command `{command}` removed successfully."
                )
            else:
                await inter.followup.send(f"The command `{command}` does not exist.")

        except Exception as e:
            print(f"Error deleting command: {e}")
            await inter.followup.send("Error deleting command.")

    async def fetch_customcommands_embeds(self, guild_id, position):
        try:
            custom_commands = list(await self.db_handler.list_customcommands(guild_id))

            if not custom_commands:
                return None, 0

            total_items = len(custom_commands)
            start_index = position * 20
            end_index = min(start_index + 20, total_items)
            commands_list = "\n".join(
                [
                    f"{index + 1}. **>{cmd}**"
                    for index, cmd in enumerate(
                        custom_commands[start_index:end_index], start=start_index
                    )
                ]
            )

            embed = disnake.Embed(
                title="Custom Commands List",
                description=commands_list,
                color=disnake.Color.orange(),
            )
            embed.set_footer(
                text=f"Page {position + 1} of {((total_items - 1) // 20) + 1}"
            )

            return embed, total_items
        except Exception as e:
            print(f"Error creating embed for custom commands: {e}")
            return None, 0

    @custom_commands.sub_command(
        name="list", description="List all custom commands for the server."
    )
    async def list(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        guild_id = inter.guild.id
        position = 0

        embed, total_items = await self.fetch_customcommands_embeds(guild_id, position)
        if not embed:
            await inter.followup.send("No custom commands found.")
            return

        async def button_callback(interaction: disnake.MessageInteraction):
            custom_id = interaction.data["custom_id"].split(":")
            action, new_position = custom_id[0], int(custom_id[1])

            if action == "previous":
                new_position = max(new_position - 1, 0)
            elif action == "next":
                new_position = min(new_position + 1, (total_items - 1) // 20)

            new_embed, _ = await self.fetch_customcommands_embeds(
                guild_id, new_position
            )
            await interaction.response.edit_message(
                embed=new_embed, view=create_pagination_view(new_position)
            )

        def create_pagination_view(current_position):
            view = disnake.ui.View()
            prev_button = disnake.ui.Button(
                label="Previous",
                style=disnake.ButtonStyle.red,
                custom_id=f"previous:{current_position}",
                disabled=(current_position == 0),
            )
            next_button = disnake.ui.Button(
                label="Next",
                style=disnake.ButtonStyle.green,
                custom_id=f"next:{current_position}",
                disabled=(current_position == (total_items - 1) // 20),
            )
            prev_button.callback = button_callback
            next_button.callback = button_callback
            view.add_item(prev_button)
            view.add_item(next_button)
            return view

        await inter.followup.send(
            embed=embed, view=create_pagination_view(position), ephemeral=True
        )

    """
    @custom_commands.sub_command(
        name="list", description="List all custom commands for the server."
    )
    async def list(self, inter: disnake.ApplicationCommandInteraction):
        guild_id = inter.guild.id
        custom_commands = await self.db_handler.list_customcommands(guild_id)

        if not custom_commands:
            await inter.send("No custom commands found.")
            return

        commands_list = "\n".join(
            [f"{index + 1}. **>{cmd}**" for index, cmd in enumerate(custom_commands)]
        )

        embed = disnake.Embed(
            title="Custom Commands List",
            description=commands_list,
            color=disnake.Color.orange(),
        )

        await inter.send(embed=embed)

    """

    @custom_commands.error
    async def custom_commands_error(
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
    bot.add_cog(customcommands(bot))
