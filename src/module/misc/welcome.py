from io import BytesIO

import requests

import config


class Welcome:
    async def welcome(self, member, guild_id):
        try:

            message, channel_id = await self.db_handler.get_welcome(guild_id)
            if not message or not channel_id:
                return

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return

            formatted_message = message.replace(
                "{member.tag}", f"{member.name}#{member.discriminator}"
            )
            formatted_message = formatted_message.replace(
                "{member.username}", f"{member.name}"
            )

            formatted_message = formatted_message.format(
                member=f"{member.mention}",
                servername=f"{member.guild.name}",
                username=f"{member.name}",
            )
            if not config.WELCOME_URL:
                url = f"{config.API_URL}/welcomecard?background=https://cdn.popcat.xyz/welcome-bg.png&text1={member.name}&text2=Welcome+To+{member.guild.name}&text3=Member+{len(member.guild.members)}&avatar={member.avatar.url}"
            else:
                url = config.WELCOME_URL

            try:
                response = requests.get(url)
                response.raise_for_status()

                output_bytes = response.content
            except Exception as e:
                print(f"Failed to download image data: {e}")

            return formatted_message, BytesIO(output_bytes), channel

        except Exception as e:
            print(f"Error sending welcome data: {e}")
            return None, None, None
