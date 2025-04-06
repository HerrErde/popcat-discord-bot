import disnake
from disnake.ext import commands

from db import DBHandler
from helpers import errors


class ticket(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_handler = DBHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Cog Ticket")
        self.db_handler = DBHandler()

    @commands.slash_command(name="ticket-setup")
    @commands.has_permissions(administrator=True)
    async def ticketsetup(self, inter: disnake.ApplicationCommandInteraction, *args):
        pass

    @ticketsetup.sub_command(name="info", description="View your current Ticket setup")
    async def info(self, inter: disnake.ApplicationCommandInteraction):

        await inter.response.defer()
        try:
            guild_id = str(inter.guild.id)
            category_id, role_id = await self.db_handler.get_ticket_info(guild_id)
            if category_id is None and role_id is None:
                response = "There is no configuration for this server!"
                await inter.followup.send(content=response)
            else:
                embed = disnake.Embed(
                    title=f"Ticket Setup Information For {inter.guild.name}",
                    color=disnake.Color.dark_grey(),
                )
                embed.add_field(
                    name="Category",
                    value=f"<#{category_id}>" if category_id is not None else "None",
                    inline=True,
                )
                embed.add_field(
                    name="Role",
                    value=f"<@&{role_id}>" if role_id is not None else "None",
                    inline=True,
                )
                await inter.followup.send(embed=embed)
        except Exception as e:
            print(f"Error ticket: {e}")
            await inter.send(
                embed=errors.create_error_embed(
                    f"Error retrieving ticket setup information: {e}", ephemeral=True
                )
            )

    @ticketsetup.sub_command(
        name="category",
        description="This will be the parent Category for all tickets created.",
    )
    async def category(
        self,
        inter: disnake.ApplicationCommandInteraction,
        category: disnake.CategoryChannel = commands.Param(description="The category"),
    ):
        try:
            guild_id = str(inter.guild.id)
            await self.db_handler.set_ticket_info(guild_id, category_id=category.id)
            await inter.send(f"Updated Ticket category to: {category.name}.")

        except Exception as e:
            print(f"Error ticket: {e}")
            await inter.send(
                embed=errors.create_error_embed(
                    f"Error setting the ticket category: {e}", ephemeral=True
                )
            )

    @ticketsetup.sub_command(
        name="role",
        description="The lowest Staff role that will be able to access the ticket channels.",
    )
    async def role(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role = commands.Param(description="The role."),
    ):
        try:
            guild_id = str(inter.guild.id)
            await self.db_handler.set_ticket_info(guild_id, role_id=role.id)
            await inter.send(f"Updated support role to: {role.name}.")

        except Exception as e:
            print(f"Error ticket: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error setting the role for tickets: {e}", ephemeral=True
                )
            )

    @ticketsetup.sub_command(
        name="panel", description="Configure a ticket panel for the server."
    )
    async def panel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(
            description="The Ticket channel."
        ),
        title: str = commands.Param(
            description="The embed title to display on the panel."
        ),
        message: str = commands.Param(
            description="The custom text to display on the panel."
        ),
        embed_color: str = commands.Param(
            description="The color of the embeds in the Ticket channel."
        ),
        button_color: str = commands.Param(
            choices=["Red", "Green", "Blue", "Grey"],
            description="The color of the button in the ticket channel.",
        ),
    ):

        await inter.response.defer()
        try:
            button_color_int = self.get_button_color(button_color)
            embed_color_int = int(embed_color, 16)

            embed = disnake.Embed(
                title=title, description=message, color=embed_color_int
            )
            embed.set_footer(text="Click On The Button Below To Create Your Ticket")
            embed.set_thumbnail(url=inter.guild.icon.url)

            button = disnake.ui.Button(
                label="Create Ticket", style=button_color_int, emoji="🎟️"
            )

            view = disnake.ui.View()
            view.add_item(button)

            async def button_callback(interaction: disnake.MessageInteraction):
                guild_id = interaction.guild.id
                user = interaction.author
                category_id, role_id = await self.db_handler.get_ticket_info(guild_id)
                category = self.bot.get_channel(category_id)

                channel_name = f"ticket-{user.name}-{user.id}"

                # Check if a channel with the same name already exists
                existing_channel = disnake.utils.get(
                    interaction.guild.text_channels, name=channel_name
                )
                if existing_channel:
                    response = "Your ticket already exists!"
                    await inter.followup.send(content=response, ephemeral=True)
                    return

                guild = interaction.guild
                user = interaction.author

                # Fetch the category channel
                category = guild.get_channel(category_id)
                if not isinstance(category, disnake.CategoryChannel):
                    raise ValueError(f"Category with ID {category_id} not found.")

                # Determine permissions for the role and the user
                role = guild.get_role(role_id)
                if role is None:
                    raise ValueError(f"Role with ID {role_id} not found.")

                overwrites = {
                    guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                    guild.me: disnake.PermissionOverwrite(view_channel=True),
                    role: disnake.PermissionOverwrite(view_channel=True),
                }

                # Include the user who initiated the interaction
                overwrites[user]: disnake.PermissionOverwrite(view_channel=True)

                ticketchannel = await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    topic=f"Click button on first message to close this ticket | Modmail for {user.name}",
                    overwrites=overwrites,
                )

                ticket_embed = disnake.Embed(
                    title="New Ticket",
                    description=f"**User:** {user.name}\n**ID:** {user.id}",
                    color=disnake.Color.orange(),
                )
                ticket_embed.set_author(
                    name=inter.author.name,
                    icon_url=inter.author.avatar.url if inter.author.avatar else None,
                )

                ticket_embed.set_footer(text="Click on the lock to close this ticket.")

                close_button = disnake.ui.Button(
                    label="Close", style=disnake.ButtonStyle.red, emoji="🔒"
                )

                async def close_ticket_callback(
                    # Ensure interaction argument is defined here
                    interaction: disnake.MessageInteraction,
                ):
                    channel = interaction.channel
                    await channel.delete()

                    # Send a private message to the user
                    user = channel.guild.get_member(channel.topic.split("for ")[1])

                    try:
                        dm_message = f"Your ticket in **{guild.name}** has been closed by **{user}**"
                        await user.send(dm_message)
                    except disnake.errors.HTTPException as e:
                        print(f"Failed to send DM to {user}: {e}")

                ticket_view = disnake.ui.View()
                ticket_view.add_item(close_button)
                close_button.callback = close_ticket_callback  # Assign callback here

                await ticketchannel.send(embed=ticket_embed, view=ticket_view)

                response = f"Your ticket has been created in <#{ticketchannel.id}>"
                await inter.followup.send(content=response, ephemeral=True)

                try:
                    dm_message = (
                        f"Your ticket in **{guild.name}** has been closed by **{user}**"
                    )
                    await user.send(dm_message)
                except disnake.errors.HTTPException as e:
                    print(f"Failed to send DM to {user}: {e}")

            button.callback = button_callback

            await channel.send(embed=embed, view=view)
            await inter.followup.send(
                f":white_check_mark: Successfully Set Up This Server's Ticket Panel In {channel.mention}!",
                ephemeral=True,
            )

        except Exception as e:
            print(f"Error ticket: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(
                    f"Error configuring the ticket panel: {e}", ephemeral=True
                )
            )

    def get_button_color(self, color: str) -> disnake.ButtonStyle:
        style_map = {
            "Red": disnake.ButtonStyle.red,
            "Green": disnake.ButtonStyle.green,
            "Blue": disnake.ButtonStyle.blurple,
            "Grey": disnake.ButtonStyle.grey,
        }
        return style_map.get(color.capitalize())

    @commands.slash_command(name="ticket", description="Open a Ticket in the Server")
    async def ticket(
        self,
        inter: disnake.ApplicationCommandInteraction,
        topic: str = commands.Param(description="The purpose of the ticket"),
    ):

        await inter.response.defer()
        try:
            guild_id = str(inter.guild.id)
            status = await self.db_handler.get_ticket_info(guild_id)
            if not status:
                response = (
                    "You need to set up the ticket system first! Use /ticket-setup."
                )

            guild_id = inter.guild.id
            user = inter.author
            category_id, role_id = await self.db_handler.get_ticket_info(guild_id)
            category = self.bot.get_channel(category_id)

            channel_name = f"ticket-{user.name}-{user.id}"

            # Check if a channel with the same name already exists
            existing_channel = disnake.utils.get(
                inter.guild.text_channels, name=channel_name
            )
            if existing_channel:
                response = "Your ticket already exists!"
                await inter.response.send_message(content=response, ephemeral=True)
                return

            guild = inter.guild
            user = inter.author

            # Fetch the category channel
            category = guild.get_channel(category_id)
            if not isinstance(category, disnake.CategoryChannel):
                raise ValueError(f"Category with ID {category_id} not found.")

            # Determine permissions for the role and the user
            role = guild.get_role(role_id)
            if role is None:
                raise ValueError(f"Role with ID {role_id} not found.")

            overwrites = {
                guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                guild.me: disnake.PermissionOverwrite(view_channel=True),
                role: disnake.PermissionOverwrite(view_channel=True),
            }

            # Include the user who initiated the interaction
            overwrites[user]: disnake.PermissionOverwrite(view_channel=True)

            ticketchannel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                topic=f"Click button on first message to close this ticket | Modmail for {user.name}",
                overwrites=overwrites,
            )

            ticket_embed = disnake.Embed(
                title="New Ticket",
                description=f"**User:** {user.name}\n**ID:** {user.id}\n**Ticket Topic:** {topic}",
                color=disnake.Color.orange(),
            )
            ticket_embed.set_author(
                name=inter.author.name,
                icon_url=inter.author.avatar.url if inter.author.avatar else None,
            )

            ticket_embed.set_footer(text="Click on the lock to close this ticket.")

            close_button = disnake.ui.Button(
                label="Close", style=disnake.ButtonStyle.red, emoji="🔒"
            )

            async def close_ticket_callback(
                # Ensure interaction argument is defined here
                interaction: disnake.MessageInteraction,
            ):
                channel = interaction.channel
                guild = interaction.guild

                # Split the topic to get the user ID
                name_parts = channel.name.split("-")
                if len(name_parts) != 3:
                    print(
                        f"Invalid name format in channel {channel.name}: {channel.topic}"
                    )
                    return

                try:
                    user_id = int(name_parts[2])
                except ValueError:
                    print(
                        f"Invalid user ID format in channel {channel.name}: {user_id}"
                    )
                    return

                user = guild.get_member(user_id)
                if not user:
                    print(f"User with ID {user_id} not found.")
                    return

                try:
                    await channel.delete()
                    dm_message = f"Your ticket in **{guild.name}** has been closed by **{interaction.author}**"
                    await user.send(dm_message)
                except disnake.errors.HTTPException as e:
                    print(f"Failed to send DM to {user}: {e}")

            ticket_view = disnake.ui.View()
            ticket_view.add_item(close_button)
            close_button.callback = close_ticket_callback  # Assign callback here

            await ticketchannel.send(embed=ticket_embed, view=ticket_view)

            response = f"Your ticket has been created in <#{ticketchannel.id}>"
            await inter.followup.send(content=response, ephemeral=True)

        except Exception as e:
            print(f"Error ticket: {e}")
            await inter.response.send_message(
                embed=errors.create_error_embed(f"Error ticket: {e}", ephemeral=True)
            )

    @ticketsetup.error
    async def ticketsetup_error(
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
    bot.add_cog(ticket(bot))
