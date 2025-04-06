import asyncio
import os
import platform

import config
import disnake
from disnake.ext import commands, tasks

from db import DBHandler, RedisHandler

if config.VOTING_HOOK:
    import topgg

    from helpers import webhook

    client = disnake.Client()
    webhook_manager = topgg.WebhookManager().set_data(client).endpoint(webhook.endpoint)
    dblclient = topgg.DBLClient(config.VOTING_KEY).set_data(client)

    @client.event
    async def on_ready():
        assert client.user is not None
        dblclient.default_bot_id = client.user.id

        if not webhook_manager.is_running:
            await webhook_manager.start(config.VOTING_PORT)


# Cache expires in 24 hours
"""
req_back = ["sqlite", "memory", "redis", "mongodb", "filesystem"]

if config.REQ_CACHE_BACK in req_back:
    if config.REQ_CACHE_BACK == "sqlite":
        backend = SQLiteCache("cache/http.sqlite")

    requests_cache.install_cache(
        "cache", backend=backend, expire_after=config.REQ_CACHE_EXP
    )
"""
"""
requests_cache.install_cache("cache", expire_after=config.REQ_CACHE_EXP)
"""

sharding_file = os.path.isfile("SHARDING")

# Setting up the bot
if config.SHARDING or sharding_file:
    bot = commands.AutoShardedInteractionBot(
        intents=disnake.Intents.all(),
        owner_ids=config.OWNER_USER_IDS,
        reload=config.DEBUG,
    )
else:
    bot = commands.InteractionBot(
        intents=disnake.Intents.all(),
        owner_ids=config.OWNER_USER_IDS,
        reload=config.DEBUG,
    )


# On Ready
@bot.event
async def on_ready():

    print("")
    print("===============================================")
    print("The bot is ready!")
    print(f"Logged in as {bot.user.name}#{bot.user.discriminator} | {bot.user.id}")
    if config.SHARDING:
        print(f"Started Sharding with {len(bot.shards)} shards")
    print(f"I am on {len(bot.guilds)} server")
    unique_users = set(
        user.id for guild in bot.guilds for user in guild.members if not user.bot
    )
    print(
        f"With {len(unique_users)} unique user{'s' if len(unique_users) != 1 else ''}"
    )
    print(f"Running on {platform.system()} {platform.release()} ({os.name})")
    print(f"Bot Version: {config.VERSION}")
    print(f"Disnake version: {disnake.__version__}")
    print(f"Python version: {platform.python_version()}")
    print("===============================================")
    print("")
    print("")
    print("================== Loaded Cogs ================")
    status_task.start()
    await asyncio.sleep(0.01)
    print("===============================================")


# Status Task
@tasks.loop()
async def status_task():
    await bot.change_presence(
        activity=disnake.Activity(type=disnake.ActivityType.listening, name="/help")
    )


# Load Cogs On Start
cog_files = {
    "voting.py": config.VOTING_ENABLE,
    "chatbot.py": config.CHATBOT_ENABLE,
}

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        if filename in cog_files:
            if cog_files[filename]:  # Check if the corresponding config flag is enabled
                bot.load_extension(f"cogs.{filename[:-3]}")
        else:
            bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    db_handler = DBHandler()
    redis_handler = RedisHandler()

    await db_handler.initialize()
    await redis_handler.initialize()

    try:
        await bot.start(config.TOKEN, reconnect=True)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Shutting down...")
        await bot.close()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
