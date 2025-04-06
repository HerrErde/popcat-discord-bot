import warnings
from datetime import datetime

import config
from cryptography.utils import CryptographyDeprecationWarning
from pymongo import MongoClient

# Suppress the CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)


db_host = config.MONGODB_HOST
db_user = config.MONGODB_USER
db_pass = config.MONGODB_PASS
db_cluster = config.MONGODB_CLUSTER
db_name = config.MONGODB_NAME

MONGODB_URI = f"mongodb+srv://{db_user}:{db_pass}@{db_host}/?retryWrites=true&w=majority&appName={db_cluster}"


class MongoDBHandler:
    def __init__(self):
        # Initialize MongoDB client and database connection
        self.client = MongoClient(MONGODB_URI)
        self.db_name = db_name
        self.db = self.client[self.db_name]  # Access the specified database

    def upsert_guild(self, guild_id):
        # Update guild data or insert if not present
        try:
            collection_name = str(
                guild_id
            )  # Ensure guild_id is converted to string if necessary
            self.db[collection_name].update_one(
                {f"guild.{guild_id}": {"$exists": True}},
                {
                    "$setOnInsert": {
                        f"guild.{guild_id}": {"users": [], "customcommands": []}
                    }
                },
                upsert=True,
            )
        except Exception as e:
            print(f"Error upserting guild data: {e}")

    def remove_guild(self, guild_id):
        # Remove the entire guild from the database
        self.db[str(guild_id)].update_one(
            {},  # Update all documents in the collection
            {"$unset": {f"guild.{guild_id}": ""}},
        )

    def upsert_user(self, guild_id, user_id):
        # Update user data within a specific guild or insert if not present
        self.db[str(guild_id)].update_one(
            {f"guild.{guild_id}.users.user_id": user_id},
            {
                "$setOnInsert": {
                    f"guild.{guild_id}.users.$.guessthecountry": [],
                    f"guild.{guild_id}.users.$.economy": [],
                }
            },
            upsert=True,
        )

    def upsert_guessthecountry(self, guild_id, user_id, country, guess_amount):
        # Add a new guessthecountry game to the user's list of games
        self.db[str(guild_id)].update_one(
            {f"guild.{guild_id}.users.user_id": user_id},
            {
                "$push": {
                    f"guild.{guild_id}.users.$.guessthecountry": {
                        "country": country,
                        "guesses": guess_amount,
                        "time": datetime.now().isoformat(),
                    }
                }
            },
        )

    def upsert_economy(self, guild_id, user_id, wallet=0, bank=0):
        # Update economy data for a user within a guild
        update_fields = {
            f"{guild_id}.users.$.economy.wallet": wallet,
            f"{guild_id}.users.$.economy.bank": bank,
        }
        self.db[str(guild_id)].update_one(
            {f"{guild_id}.users.user_id": user_id},
            {"$set": update_fields},
            upsert=True,
        )

    def add_customcommand(self, guild_id, trigger, response):
        try:
            collection_name = str(guild_id)
            guild_collection = self.db[collection_name]

            # Check if the custom command already exists
            existing_command = guild_collection.find_one(
                {f"{guild_id}.customcommands.{trigger}": {"$exists": True}}
            )

            if existing_command:
                return True  # Command already exists

            # Add the custom command to the guild
            guild_collection.update_one(
                {f"{guild_id}": {"$exists": True}},
                {
                    "$set": {
                        f"guild.{guild_id}.customcommands.{trigger}": response,
                    }
                },
                upsert=True,
            )
            return False  # Command added successfully

        except Exception as e:
            print(f"Error adding custom command: {e}")
            return True

    def remove_customcommand(self, guild_id, trigger):
        # Remove a custom command from the guild
        result = self.db[str(guild_id)].update_one(
            {f"{guild_id}.customcommands.{trigger}": {"$exists": True}},
            {"$unset": {f"{guild_id}.customcommands.{trigger}": ""}},
        )
        return result.modified_count > 0

    def list_customcommands(self, guild_id):
        guild_data = self.db[str(guild_id)].find_one(
            {guild_id: {guild_id: {"$exists": True}}}
        )
        if guild_data and "customcommands" in guild_data.get("guilds", {}).get(
            guild_id, {}
        ):
            return list(guild_data["guilds"][guild_id]["customcommands"].keys())
        else:
            return []

    def get_customcommand(self, guild_id, trigger):
        result = self.db[str(guild_id)].find_one(
            {f"{guild_id}.customcommands.{trigger}": {"$exists": True}}
        )

        if result:
            return result[f"guild.{guild_id}.customcommands.{trigger}"]
        else:
            return None

    def set_clicker(self, guild_id, user_id, count):
        update_fields = {f"guild.{guild_id}.users.$.clicker": count}
        self.db[str(guild_id)].update_one(
            {f"guild.{guild_id}.users.user_id": user_id},
            {"$set": update_fields},
            upsert=True,
        )

    def list_clicker(self, guild_id):
        # Use aggregation to count clicker events for each user in the guild
        pipeline = [
            {"$match": {"guilds.guild_id": guild_id}},
            {"$unwind": "$guilds"},
            {"$unwind": "$guilds.users"},
            {
                "$group": {
                    "_id": "$guilds.users.user_id",
                    "count": {"$sum": "$guilds.users.clicker"},
                }
            },
        ]

        result = list(self.db[str(guild_id)].aggregate(pipeline))

        # Format the result as {user_id: count} dictionary
        user_counts = {user["_id"]: user["count"] for user in result}

        return user_counts
