import time
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import errors

import config

db_host = config.DB_HOST
db_user = config.DB_USER
db_pass = config.DB_PASS
db_cluster = config.DB_CLUSTER

# Ensure the MONGODB_URI is correctly formatted
MONGODB_URI = f"mongodb+srv://{db_user}:{db_pass}@{db_host}/?retryWrites=true&w=majority&appName={db_cluster}"


class DBHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBHandler, cls).__new__(cls)
        return cls._instance

    async def initialize(self):
        if hasattr(self, "initialized") and self.initialized:
            return  # Already initialized, so do nothing

        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                self.client = AsyncIOMotorClient(
                    MONGODB_URI,
                    serverSelectionTimeoutMS=10000,  # Increased timeout
                    readPreference="secondaryPreferred",  # Allow secondary read preference
                )
                self.client.admin.command("ping")
                self.db_guilds = self.client["guilds"]
                self.db_users = self.client["users"]
                self.db_test = self.client["test"]
                self.initialized = True
                print("Successfully connected to MongoDB")
                return  # Successful connection
            except errors.ServerSelectionTimeoutError as e:
                retries += 1
                print(
                    f"Server selection timeout error, retrying... ({retries}/{max_retries})"
                )
                time.sleep(5)  # Increased delay between retries
            except errors.ConfigurationError as e:
                print(f"ConfigurationError: {e}")
                break
            except errors.ConnectionFailure as e:
                print(f"ConnectionFailure: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
        else:
            print("Max retries reached. Could not connect to MongoDB.")

    async def check_performance(self):
        """
        Check MongoDB server performance including ping time, read speed, and write speed.
        Also includes the size of all databases except "test" and the MongoDB version and cluster location.

        :return: A dictionary with performance metrics and database sizes.
        """
        performance = {}

        # Get MongoDB version
        try:
            build_info = await self.client.admin.command("buildInfo")
            performance["version"] = build_info["version"]
        except Exception:
            performance["version"] = None

        # Get MongoDB cluster location
        try:
            host_info = await self.client.admin.command("hostInfo")
            performance["cluster_location"] = host_info["system"]["hostname"]
        except Exception:
            performance["cluster_location"] = None

        # Ping the server
        try:
            start_time = time.time()
            await self.client.admin.command("ping")
            ping_time = round(
                (time.time() - start_time) * 1000, 2
            )  # Convert to milliseconds
            performance["ping"] = ping_time
        except Exception:
            performance["ping"] = None

        # Write speed test
        try:
            collection_name = "test"
            collection = self.db_test[collection_name]
            start_time = time.time()
            test_doc = {"test": "write_speed"}
            await collection.insert_one(test_doc)
            write_time = round(
                (time.time() - start_time) * 1000, 2
            )  # Convert to milliseconds
            performance["write_speed"] = write_time
        except Exception:
            performance["write_speed"] = None

        # Read speed test
        try:
            await collection.insert_one({"test": "read_speed"})
            start_time = time.time()
            await collection.find_one({"test": "read_speed"})
            read_time = round(
                (time.time() - start_time) * 1000, 2
            )  # Convert to milliseconds
            performance["read_speed"] = read_time
        except Exception:
            performance["read_speed"] = None

        # Clean up test data
        try:
            await collection.drop()
        except Exception:
            pass  # Ignore errors in cleanup

        # Get the size of all databases except "test"
        db_sizes = {}
        total_size = 0
        try:
            database_names = await self.client.list_database_names()
            for db_name in database_names:
                if db_name != "test":
                    try:
                        db = self.client[db_name]
                        stats = await db.command("dbstats")
                        db_sizes[db_name] = stats["dataSize"]
                        total_size += stats["dataSize"]
                    except Exception:
                        db_sizes[db_name] = None
            performance["db_sizes"] = db_sizes
            performance["total_db_size"] = total_size
        except Exception:
            performance["db_sizes"] = None
            performance["total_db_size"] = None

        return performance

    async def drop_all_databases(self):
        for db_name in await self.client.list_database_names():
            # typically you don't want to drop these
            if db_name not in ["admin", "local"]:
                await self.client.drop_database(db_name)
        return True

    async def drop_all_collections(self):
        for db_name in await self.client.list_database_names():
            # typically you don't want to drop collections in these databases
            if db_name not in ["admin", "local"]:
                db = self.client[db_name]
                for collection_name in await db.list_collection_names():
                    await db.drop_collection(collection_name)
        return True

    async def remove_guild(self, guild_id):
        try:
            collection_name = str(guild_id)
            await self.db_guilds.drop_collection(collection_name)
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error removing guild {guild_id}: {e}")
            return False  # Return False if there was an error

    async def set_guessthecountry(self, user_id, country, guess_amount):
        collection_name = str(user_id)

        try:
            # Check if the user's document exists
            user_exists = await self.db_users[collection_name].find_one(
                {"guessthecountry": {"$exists": True}}
            )

            # Update the user's game information by pushing to the guessthecountry array
            result = await self.db_users[collection_name].update_one(
                {},
                {
                    "$push": {
                        "guessthecountry": {
                            "country": country,
                            "guesses": guess_amount,
                            "date": int(time.time()),
                        }
                    }
                },
                upsert=True,  # Create the document if it does not exist
            )

            if result.modified_count > 0 or result.upserted_id:
                if config.DEBUG:
                    print(f"Updated document for user {user_id}: {result}")
                return True
            else:
                if config.DEBUG:
                    print(f"No document updated for user {user_id}")
                return False

        except Exception as e:
            if config.DEBUG:
                print(f"Error setting guessthecountry game: {e}")
            return False

    async def list_guessthecountry(self):
        collections = await self.db_users.list_collection_names()

        # Define the aggregation pipeline to count the length of guessthecountry array for each document
        pipeline = [
            {"$match": {"guessthecountry": {"$exists": True, "$ne": []}}},
            {"$project": {"length": {"$size": "$guessthecountry"}}},
        ]

        try:
            # Dictionary to hold the collection names and their respective guessthecountry array lengths
            collection_lengths = {}

            # Iterate through each collection and aggregate data
            for collection_name in collections:
                collection = self.db_users[collection_name]
                async for doc in collection.aggregate(pipeline):
                    if collection_name in collection_lengths:
                        collection_lengths[collection_name] += doc["length"]
                    else:
                        collection_lengths[collection_name] = doc["length"]

            # Sort the collections by the number of games won in descending order and take the top 10
            sorted_collections = dict(
                sorted(
                    collection_lengths.items(), key=lambda item: item[1], reverse=True
                )[:10]
            )

            return sorted_collections

        except Exception as e:
            if config.DEBUG:
                print(f"Error listing guessthecountry games: {e}")
            return {}

    async def history_guessthecountry(self, user_id):
        collection_name = str(user_id)
        pipeline = [
            {"$match": {"guessthecountry": {"$exists": True, "$ne": []}}},
            {
                "$project": {
                    "guessthecountry": 1,
                    "_id": 0,
                }
            },
            {"$unwind": "$guessthecountry"},
            {"$replaceRoot": {"newRoot": "$guessthecountry"}},
        ]
        try:
            cursor = self.db_users[collection_name].aggregate(pipeline)

            # Initialize dictionary to hold historical data
            history_dict = {"history": []}

            async for doc in cursor:
                history_dict["history"].append(
                    {
                        "country": doc.get("country", ""),
                        "guesses": doc.get("guesses", ""),
                        "date": doc.get("date", ""),
                    }
                )

            return history_dict

        except Exception as e:
            if config.DEBUG:
                print(f"Error listing guessthecountry games: {e}")
            return {"history": []}

    async def clicker_set(self, guild_id, user_id):
        collection_name = str(guild_id)
        try:
            # Ensure the 'clicker' field exists in any document, initialize if not
            await self.db_guilds[collection_name].update_many(
                {},
                {"$setOnInsert": {"clicker": {}}},
                upsert=True,
            )

            # Increment the user's click count in all documents
            update_result = await self.db_guilds[collection_name].update_many(
                {},
                {"$inc": {f"clicker.{user_id}": 1}},
            )

            return True if update_result.modified_count > 0 else False

        except Exception as e:
            print(f"Error updating clicker: {e}")
            return None

    async def clicker_total(self, guild_id):
        collection_name = str(guild_id)

        if config.DEBUG:
            print(f"Debug: Database Collection: {collection_name}")

        # Check if any document contains the 'clicker' field
        result_check = await self.db_guilds[collection_name].find_one(
            {"clicker": {"$exists": True}}
        )
        if not result_check:
            if config.DEBUG:
                print(f"No 'clicker' field found in collection {collection_name}")
            return 0

        pipeline = [
            {"$match": {}},
            {"$project": {"clicker_values": {"$objectToArray": "$clicker"}}},
            {"$unwind": "$clicker_values"},  # Unwind the 'clicker' array
            {"$group": {"_id": None, "total_clicker": {"$sum": "$clicker_values.v"}}},
        ]

        if config.DEBUG:
            print(f"Debug: Aggregation Pipeline: {pipeline}")

        result = (
            await self.db_guilds[collection_name].aggregate(pipeline).to_list(length=1)
        )

        if config.DEBUG:
            print(f"Debug: Aggregation Result: {result}")

        return result[0]["total_clicker"] if result else 0

    async def clicker_leaderboard(self, guild_id):
        collection_name = str(guild_id)

        pipeline = [
            {
                "$match": {"clicker": {"$exists": True}}
            },  # Only documents that contain 'clicker'
            {
                "$project": {"_id": 0, "user_id": {"$objectToArray": "$clicker"}}
            },  # Convert 'clicker' object to array
            {
                "$unwind": "$user_id"
            },  # Unwind the array to have individual documents for each user
            {
                "$group": {"_id": "$user_id.k", "amount": {"$sum": "$user_id.v"}}
            },  # Sum click counts for each user
            {"$sort": {"amount": -1}},  # Sort by click count in descending order
        ]

        cursor = (
            await self.db_guilds[collection_name]
            .aggregate(pipeline)
            .to_list(length=None)
        )

        clicker_dict = {}
        for doc in cursor:
            clicker_dict[doc["_id"]] = doc["amount"]

        return clicker_dict

    async def add_customcommand(self, guild_id, trigger, response):
        collection_name = str(guild_id)
        try:
            # Check if the custom command already exists
            existing_command = await self.db_guilds[collection_name].find_one(
                {f"customcommands.{trigger}": {"$exists": True}}
            )

            if existing_command:
                return True  # Command already exists
            else:
                # Add the custom command to the guild
                await self.db_guilds[collection_name].update_one(
                    {},
                    {
                        "$set": {
                            f"customcommands.{trigger}": response,
                        }
                    },
                    upsert=True,
                )
                return False  # Command added successfully

        except Exception as e:
            print(f"Error creating custom command: {e}")
            return None

    async def remove_customcommand(self, guild_id, trigger):
        collection_name = str(guild_id)
        # Remove a custom command from the guild
        result = await self.db_guilds[collection_name].update_one(
            {f"customcommands.{trigger}": {"$exists": True}},
            {"$unset": {f"customcommands.{trigger}": ""}},
        )
        return result.modified_count > 0

    async def get_customcommand(self, guild_id, trigger):
        collection_name = str(guild_id)
        try:
            # Retrieve the custom command from MongoDB
            result = await self.db_guilds[collection_name].find_one(
                {f"customcommands.{trigger}": {"$exists": True}}
            )

            # Debugging: print the retrieved result
            if config.DEBUG:
                print(
                    f"Retrieved document for guild_id '{guild_id}' and trigger '{trigger}': {result}"
                )

            if result:
                return result["customcommands"][trigger]
            else:
                return None

        except Exception as e:
            if config.DEBUG:
                print(
                    f"Error retrieving custom command for guild_id '{guild_id}' and trigger '{trigger}': {e}"
                )
            return None

    async def list_customcommands(self, guild_id):
        collection_name = str(guild_id)
        try:
            result = await self.db_guilds[collection_name].find_one(
                {"customcommands": {"$exists": True}}
            )

            if result:
                if config.DEBUG:
                    print(
                        f"Custom commands found for guild {guild_id}: {result['customcommands'].keys()}"
                    )
                return result[
                    "customcommands"
                ].keys()  # Return keys from customcommands

            else:
                if config.DEBUG:
                    print(f"No custom commands found for guild {guild_id}")
                return []  # Return empty list if no custom commands found

        except Exception as e:
            print(f"Error retrieving custom commands for guild {guild_id}: {e}")
            return []

    async def set_userbio(self, user_id, text):
        collection_name = str(user_id)
        try:
            await self.db_users[collection_name].update_one(
                {},
                # Update operation using $set to set bio field
                {"$set": {"bio": text}},
                upsert=True,
            )
            return True
        except Exception as e:
            print(f"Error updating bio for user {user_id}: {e}")
            return False

    async def get_userbio(self, user_id):
        collection_name = str(user_id)
        try:
            user_data = await self.db_users[collection_name].find_one({})
            if user_data:
                return user_data.get("bio", "")
            else:
                return "No Bio Set"
        except Exception as e:
            print(f"Error fetching bio for user {user_id}: {e}")
            return None

    async def add_todo(self, user_id, title, description):
        collection_name = str(user_id)
        try:
            # async define the new todo item
            new_todo = {"title": title, "description": description}

            # Update the user's collection by adding the new todo item to the 'todo' array
            await self.db_users[collection_name].update_one(
                {},
                # Add new_todo to the 'todo' array
                {"$push": {"todo": new_todo}},
                upsert=True,
            )
            return True
        except Exception as e:
            print(f"Error adding todo item for user {user_id}: {e}")
            return False

    async def remove_todo(self, user_id, title):
        collection_name = str(user_id)
        try:
            user_document = await self.db_users[collection_name].find_one({})

            if user_document and "todo" in user_document:
                # Find the index of the last occurrence of the todo item with the given title
                last_index = None
                for idx, todo in enumerate(reversed(user_document["todo"])):
                    if todo.get("title") == title:
                        last_index = len(user_document["todo"]) - 1 - idx
                        break

                if last_index is not None:
                    # Remove the todo item at the identified index
                    await self.db_users[collection_name].update_one(
                        {}, {"$unset": {f"todo.{last_index}": ""}}
                    )

                    # Clean up the array after removal
                    await self.db_users[collection_name].update_one(
                        {}, {"$pull": {"todo": None}}
                    )

                    return True

            return False

        except Exception as e:
            print(f"Error removing todo item for user {user_id}: {e}")
            return False

    async def list_todo(self, user_id):
        collection_name = str(user_id)
        try:
            # Get the document for the user
            user_document = await self.db_users[collection_name].find_one({})

            # If the document exists and has a 'todo' field, return it
            if user_document and "todo" in user_document:
                return user_document["todo"]
            else:
                return []
        except Exception as e:
            print(f"Error getting todo list for user {user_id}: {e}")
            return []

    async def set_welcome(self, guild_id, channel_id):
        collection_name = str(guild_id)
        try:
            await self.db_guilds[collection_name].update_one(
                {},
                {
                    "$set": {"welcome.channel": channel_id}
                },  # Add welcome channel to the 'welcome' array
                upsert=True,
            )
            return True
        except Exception as e:
            if config.DEBUG:
                print(
                    f"Error setting welcome channel in guild {guild_id} to channel {channel_id}: {e}"
                )
            return False  # Return False if update fails

    async def set_welcome_msg(self, guild_id, message):
        collection_name = str(guild_id)
        try:
            # Update the welcome message in the database
            await self.db_guilds[collection_name].update_one(
                {}, {"$set": {"welcome.message": message}}, upsert=True
            )
            return True

        except Exception as e:
            if config.DEBUG:
                print(f"Error setting welcome message for guild {guild_id}: {e}")
            return False

    async def get_welcome(self, guild_id):
        collection_name = str(guild_id)
        try:
            # Query for any document in the collection, as we expect only one per guild
            document = await self.db_guilds[collection_name].find_one({})
            if document and "welcome" in document:
                return document["welcome"].get("message"), document["welcome"].get(
                    "channel"
                )
            return None, None
        except Exception as e:
            if config.DEBUG:
                print(f"Error retrieving welcome data for guild {guild_id}: {e}")
            return None, None

    async def remove_welcome(self, guild_id):
        collection_name = str(guild_id)
        try:
            # Use an appropriate query to remove the welcome data
            result = await self.db_guilds[collection_name].update_one(
                {}, {"$unset": {"welcome": ""}}
            )
            if result.modified_count > 0:
                return True
            else:
                if config.DEBUG:
                    print(f"No welcome data found to remove for guild {guild_id}.")
                return False  # Return False if no documents were modified
        except Exception as e:
            if config.DEBUG:
                print(f"Error removing welcome data from {guild_id}: {e}")
            return False  # Return False if the update fails

    async def upsert_economy(self, user_id):
        collection_name = str(user_id)

        try:
            # Check if any documents exist in the collection
            document_count = await self.db_users[collection_name].count_documents({})

            if document_count == 0:
                # No documents exist, perform upsert
                result = await self.db_users[collection_name].update_one(
                    {},
                    {
                        "$set": {
                            "economy": {
                                "pocket": 2000,
                                "bank": 0,
                                "karma": 0,
                                "inventory": {},
                            }
                        },
                        "stocks": [],
                    },
                    upsert=True,  # Create a new document if none exists
                )
                if result.upserted_id is not None:
                    # A new document was inserted
                    return True, True
                else:
                    # No document was inserted (possible if the collection was modified in between)
                    return True, False

            else:
                # Documents exist, check if 'economy' field exists in at least one document
                result = await self.db_users[collection_name].update_many(
                    {
                        "economy": {"$exists": False}
                    },  # Filter to find documents without 'economy'
                    {
                        "$set": {
                            "economy": {
                                "pocket": 2000,
                                "bank": 0,
                                "karma": 0,
                                "inventory": {},
                            }
                        }
                    },
                )

                if result.matched_count == 1 and result.modified_count == 1:
                    # Documents matched and were updated
                    return True, True
                elif result.matched_count == 1 and result.modified_count == 0:
                    # Documents matched but no fields were updated
                    return True, False
                else:
                    # No documents matched the filter, meaning all documents already have 'economy'
                    return True, False

        except Exception as e:
            if config.DEBUG:
                print(f"Error upserting economy data for user {user_id}: {e}")
            return False, False  # Return False, False if there was an error

    async def money_balance(self, user_id):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            user_data = await self.db_users[collection_name].find_one({})
            economy = user_data.get("economy", {}) if user_data else None

            if economy:
                pocket = economy.get("pocket")
                bank = economy.get("bank")
                return pocket, bank
            return 0, 0

        except Exception as e:
            if config.DEBUG:
                print(f"Error retrieving balance for user {user_id}: {e}")
            return 0, 0

    async def money_move(self, user1_id, user2_id, amount):
        collection_name1 = str(user1_id)
        collection_name2 = str(user2_id)

        user1_exists = (
            await self.db_users[collection_name1].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user1_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user1_id)

        user2_exists = (
            await self.db_users[collection_name1].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user2_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user2_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Deduct money from sender
                    result = await self.db_users[collection_name1].update_one(
                        {
                            "economy.pocket": {"$gte": amount}
                        },  # Ensure user has enough money
                        {"$inc": {"economy.pocket": -amount}},
                        session=session,
                    )

                    # Check if the deduction was successful
                    if result.matched_count == 0:
                        await session.abort_transaction()
                        if config.DEBUG:
                            print(f"Error: User {user1_id} does not have enough money.")
                        return False

                    # Add money to receiver
                    await self.db_users[collection_name2].update_one(
                        {},
                        {"$inc": {"economy.pocket": amount}},
                        upsert=True,
                        session=session,
                    )

                    await session.commit_transaction()

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(
                            f"Error transferring money from user {user1_id} to user {user2_id}: {e}"
                        )
                    return False

                return True

    async def money_daily(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            now = datetime.datetime.utcnow()
            # Get the start of the current UTC day (00:00:00)
            start_of_today = datetime.datetime(
                now.year, now.month, now.day, 0, 0, 0, 0, datetime.timezone.utc
            )
            start_of_today_timestamp = int(start_of_today.timestamp())

            # Query the user's data
            user_data = await self.db_users[collection].find_one({})

            last_claim_timestamp = user_data.get("economy", {}).get("last_daily", 0)

            if last_claim_timestamp >= start_of_today_timestamp:
                # If the user has already claimed today, return the remaining time
                remaining_time = (
                    start_of_today_timestamp + 86400 - now.timestamp()
                )  # 86400 seconds in a day
                hours, remainder = divmod(remaining_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                return False, (int(hours), int(minutes), int(seconds))

            # Update the user's balance and last daily claim time
            await self.db_users[collection].update_one(
                {},
                {
                    "$inc": {"economy.pocket": amount},
                    "$set": {"economy.last_daily": start_of_today_timestamp},
                },
                upsert=True,
            )
            return True, None

        except Exception as e:
            if config.DEBUG:
                print(f"Error using getting daily money from user {user_id}: {e}")
            return False

    async def money_mansion(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            user_data = await self.db_users[collection_name].find_one({})

            # Check if the user has a Mansion
            has_mansion = "Mansion" in user_data.get("economy", {}).get("inventory", [])
            if not has_mansion:
                return False, False

            now = datetime.datetime.utcnow()
            # Get the start of the current UTC week (Monday 00:00:00)
            start_of_week = now - datetime.timedelta(days=now.weekday())
            start_of_week = datetime.datetime(
                start_of_week.year,
                start_of_week.month,
                start_of_week.day,
                0,
                0,
                0,
                0,
                datetime.timezone.utc,
            )
            start_of_week_timestamp = int(start_of_week.timestamp())

            # Query the user's data
            user_data = await self.db_users[collection_name].find_one({})

            last_claim_timestamp = user_data.get("economy", {}).get("last_mansion", 0)

            if last_claim_timestamp >= start_of_week_timestamp:
                # If the user has already claimed this week, return the remaining time
                # 604800 seconds in a week
                remaining_time = start_of_week_timestamp + 604800 - now.timestamp()
                days, remainder = divmod(remaining_time, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                return False, (int(days), int(hours), int(minutes), int(seconds))

            # Update the user's balance and last weekly claim time
            await self.db_users[collection_name].update_one(
                {},
                {
                    "$inc": {"economy.pocket": amount},
                    "$set": {"economy.last_mansion": start_of_week_timestamp},
                },
                upsert=True,
            )
            return True, None

        except Exception as e:
            if config.DEBUG:
                print(f"Error using mansion item from user {user_id}: {e}")
            return False

    async def money_deposit(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Deduct money from user's pocket
                    result = await self.db_users[collection_name].update_one(
                        {
                            "economy.pocket": {"$gte": amount}
                        },  # Ensure user has enough money
                        {"$inc": {"economy.pocket": -amount}},
                        session=session,
                    )

                    # Check if the deduction was successful
                    if result.matched_count == 0:
                        await session.abort_transaction()
                        if config.DEBUG:
                            print(f"Error: User {user_id} does not have enough money.")
                        return False

                    # Add money to user's bank
                    await self.db_users[collection_name].update_one(
                        # Match specific document
                        {"economy": {"$exists": True}},
                        {"$inc": {"economy.bank": amount}},
                        session=session,
                    )

                    await session.commit_transaction()  # Fixed missing `await`

                    return True

                except Exception as e:
                    await session.abort_transaction()  # Properly await abort
                    if config.DEBUG:
                        print(
                            f"Error transferring money from user {user_id} pocket to bank: {e}"
                        )
                    return False

    async def money_withdraw(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Deduct money from user's bank
                    result = await self.db_users[collection_name].update_one(
                        # Ensure user has enough money
                        {"economy.bank": {"$gte": amount}},
                        {"$inc": {"economy.bank": -amount}},
                        session=session,
                    )

                    # Check if the deduction was successful
                    if result.matched_count == 0:
                        await session.abort_transaction()
                        if config.DEBUG:
                            print(
                                f"Error: User {user_id} does not have enough in their bank."
                            )
                        return False

                    # Add money to user's pocket
                    await self.db_users[collection_name].update_one(
                        # Match specific document
                        {"economy": {"$exists": True}},
                        {"$inc": {"economy.pocket": amount}},
                        upsert=True,
                        session=session,
                    )

                    await session.commit_transaction()

                    return True

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(
                            f"Error transferring money from user {user_id} bank to pocket: {e}"
                        )
                    return False

    async def money_slots(self, user_id, amount, is_win):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    if is_win:
                        # Add money to user's pocket
                        result = await self.db_users[collection_name].update_one(
                            {
                                "economy.pocket": {"$gte": -amount}
                                # Ensure user has enough money if amount is negative (in case of loss)
                            },
                            {"$inc": {"economy.pocket": amount}},
                            session=session,
                        )
                    else:
                        # Deduct money from user's pocket
                        result = await self.db_users[collection_name].update_one(
                            {
                                "economy.pocket": {"$gte": amount}
                            },  # Ensure user has enough money
                            {"$inc": {"economy.pocket": -amount}},
                            session=session,
                        )

                    # Check if the update was successful
                    if result.matched_count == 0:
                        await session.abort_transaction()
                        if config.DEBUG:
                            print(f"Error: User {user_id} does not have enough money.")
                        return False

                    await session.commit_transaction()

                    return True

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"Error processing transaction for user {user_id}: {e}")
                    return False  # Return False if there is an exception

    async def money_set(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            # Update user's balance and last daily claim time
            await self.db_users[collection_name].update_one(
                {},
                {
                    "$set": {"economy.pocket": amount},
                },
                upsert=True,
            )
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error setting {user_id} money amount: {e}")
            return False  # Return False if update fails

    async def money_give(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            # Update user's balance and last daily claim time
            await self.db_users[collection_name].update_one(
                {},
                {
                    "$inc": {"economy.pocket": amount},
                },
                upsert=True,
            )
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error giving {amount} of money to user {user_id}: {e}")
            return False

    async def money_remove(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            # Update user's balance and last daily claim time
            await self.db_users[collection_name].update_one(
                {"economy.pocket": {"$gte": amount}},
                {
                    "$inc": {"economy.pocket": -amount},
                },
                upsert=True,
            )
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error removing {amount} of money from from user {user_id}: {e}")
            return False

    async def money_check_inv(self, user_id, item):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            # Retrieve the user's data from the database
            user_data = await self.db_users[collection_name].find_one({})

            if user_data is None:
                return False

            # Check if the user has the Item
            has_item = item in user_data.get("economy", {}).get("inventory", [])
            if not has_item:
                return False

            return True

        except Exception as e:
            if config.DEBUG:
                print(f"Error checking if {item} exsists user {user_id} inventory: {e}")
            return False

    async def money_buy_item(self, user_id, item, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Deduct money from user's pocket
                    result = await self.db_users[collection_name].update_one(
                        {
                            "economy.pocket": {"$gte": amount}
                        },  # Ensure user has enough money
                        {
                            "$inc": {"economy.pocket": -amount}
                        },  # Deduct amount from pocket
                        session=session,
                    )

                    # Check if the deduction was successful
                    if result.matched_count == 0:
                        if config.DEBUG:
                            print(f"Error: User {user_id} does not have enough money.")
                        return False, False

                    # Try to increment the item quantity if it already exists in the inventory
                    result = await self.db_users[collection_name].update_one(
                        {
                            f"economy.inventory.{item}": {"$exists": True}
                        },  # Check if the item exists in the inventory
                        {
                            "$inc": {
                                f"economy.inventory.{item}": 1
                            }  # Increment the item quantity
                        },
                        session=session,
                    )

                    # If the item does not exist, add it with a quantity of 1
                    if result.matched_count == 0:
                        await self.db_users[collection_name].update_one(
                            {},
                            {
                                "$set": {f"economy.inventory.{item}": 1}
                            },  # Add the item with quantity 1
                            session=session,
                        )

                    return True, True  # Transaction was successful

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"Transaction error: {e}")
                    return False, False

    # TODO check if works
    async def money_give_item(self, user_id, item):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Check if the item is already in the inventory
                    item_exists = (
                        await self.db_users[collection_name].count_documents(
                            {"economy.inventory": item}, session=session
                        )
                        > 0
                    )

                    if item_exists:
                        await session.commit_transaction()
                        return True, False  # Item already exists

                    # Add the item to the user's inventory items list if it is not already there
                    await self.db_users[collection_name].update_one(
                        {"economy.inventory": {"$ne": item}},
                        {
                            "$addToSet": {"economy.inventory": item}
                        },  # Add item to the inventory if not present
                        session=session,
                    )

                    await session.commit_transaction()

                    return True, True  # Item was added successfully

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"An error occurred: {e}")
                    return False, False

    async def money_remove_item(self, user_id, item):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            # Check if the item is already in the inventory
            item_exists = (
                await self.db_users[collection_name].count_documents(
                    {"economy.inventory": item}
                )
                > 0
            )

            if item_exists:
                return True, False  # Item already exists
            return True, True

        except Exception as e:
            await session.abort_transaction()
            if config.DEBUG:
                print(f"Error removing item from user {user_id}: {e}")
            return False

    async def money_rewards(self, user_id, item, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Check if the inventory has 6 items
                    inventory_full = (
                        await self.db_users[collection_name].count_documents(
                            {"economy.inventory": {"$size": 6}}, session=session
                        )
                        > 0
                    )

                    if item or inventory_full:
                        amount += 1000
                    # Add money to user's pocket
                    await self.db_users[collection_name].update_one(
                        {},
                        {"$inc": {"economy.pocket": amount}},
                        session=session,
                    )

                    if not item:
                        # No item to add, just commit the transaction
                        await session.commit_transaction()
                        return True, False  # Money was added, no item involved

                    # Check if the item is already in the inventory
                    item_exists = (
                        await self.db_users[collection_name].count_documents(
                            {"economy.inventory": item}, session=session
                        )
                        > 0
                    )

                    if item_exists:
                        await session.commit_transaction()
                        return True, False  # Item already exists, no need to add

                    # Add the item to the user's inventory items list if it is not already there
                    await self.db_users[collection_name].update_one(
                        {"economy.inventory": {"$ne": item}},
                        {
                            "$addToSet": {"economy.inventory": item}
                        },  # Add item to the inventory if not present
                        session=session,
                    )

                    await session.commit_transaction()

                    return True, True  # Item was added successfully

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"An error occurred: {e}")
                    return False, False

    async def money_add_fish(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    user_data = await self.db_users[collection_name].find_one(
                        {}, session=session
                    )

                    # Check if the user has a Fishing Rod
                    has_fishingrod = "Fishing Rod" in user_data.get("economy", {}).get(
                        "inventory", []
                    )
                    if not has_fishingrod:
                        return False, False

                    # Add fish to user's inventory
                    await self.db_users[collection_name].update_one(
                        {},
                        {
                            "$inc": {"economy.inventory.fish": amount}
                        },  # Increment the fish count
                        upsert=True,
                        session=session,
                    )

                    await session.commit_transaction()

                    return True

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"Error adding fish for user {user_id}: {e}")
                    return False

    async def money_sell_fish(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Fetch the user's current karma
                    user = await self.db_users[collection_name].find_one(
                        {"economy.inventory.fish": {"$exists": True}},
                        {"_id": 0, "economy.inventory.fish": 1},
                        session=session,
                    )

                    # Check if the user has karma and if it's sufficient
                    if not user or user["economy"]["items"]["fish"] < amount:
                        current_karma = user["economy"]["items"]["fish"] if user else 0
                        await session.abort_transaction()
                        if config.DEBUG:
                            print(
                                f"Error: User {user_id} does not have enough fish. Current fish: {current_karma}"
                            )
                        return current_karma

                    # Deduct the karma and add to the pocket
                    result = await self.db_users[collection_name].update_one(
                        {"economy.inventory.fish": {"$gte": amount}},
                        {
                            "$inc": {
                                "economy.inventory.fish": -amount,
                                "economy.pocket": 25,
                            }
                        },
                        upsert=True,
                        session=session,
                    )

                    # Check if the deduction was successful
                    if result.matched_count == 0:
                        await session.abort_transaction()
                        print(f"Error: User {user_id} does not have enough fish.")
                        return False

                    await session.commit_transaction()

                    return True

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"Error selling fish for user {user_id}: {e}")
                    return False

    async def money_add_karma(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    user_data = await self.db_users[collection_name].find_one(
                        {}, session=session
                    )

                    # Check if the user has a Laptop
                    has_laptop = "Laptop" in user_data.get("economy", {}).get(
                        "inventory", []
                    )
                    if not has_laptop:
                        return False, False

                    # Add karma to user's inventory
                    await self.db_users[collection_name].update_one(
                        {},
                        {"$inc": {"economy.karma": amount}},
                        upsert=True,
                        session=session,
                    )

                    await session.commit_transaction()

                    return (
                        True,
                        True,
                    )

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"Error adding karma for user {user_id}: {e}")
                    return (
                        False,
                        False,
                    )

    async def money_sell_karma(self, user_id, amount):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Fetch the user's current karma
                    user = await self.db_users[collection_name].find_one(
                        {"economy.karma": {"$exists": True}},
                        {"_id": 0, "economy.karma": 1},
                        session=session,
                    )

                    # Check if the user has karma and if it's sufficient
                    if not user or user["economy"]["items"]["karma"] < amount:
                        current_karma = user["economy"]["items"]["karma"] if user else 0
                        await session.abort_transaction()
                        if config.DEBUG:
                            print(
                                f"Error: User {user_id} does not have enough karma. Current karma: {current_karma}"
                            )
                        return current_karma

                    # Deduct the karma and add to the pocket
                    result = await self.db_users[collection_name].update_one(
                        {"economy.karma": {"$gte": amount}},
                        {
                            "$inc": {
                                "economy.karma": -amount,
                                "economy.pocket": 2,
                            }
                        },
                        upsert=True,
                        session=session,
                    )

                    # Check if the deduction was successful
                    if result.matched_count == 0:
                        await session.abort_transaction()
                        if config.DEBUG:
                            print(f"Error: User {user_id} does not have enough karma.")
                        return False

                    await session.commit_transaction()

                    return True

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"Error selling karma for user {user_id}: {e}")
                    return False

    async def money_profile(self, user_id):
        collection_name = str(user_id)

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"economy": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            # Query the database for economy data
            user_data = await self.db_users[collection_name].find_one(
                {}, {"economy": 1}
            )

            if not user_data:
                return {}, 0, 0, 0

            # Extract economy data
            economy_data = user_data.get("economy", {})
            inventory_data = economy_data.get("inventory", {})
            pocket = economy_data.get("pocket", 0)
            bank = economy_data.get("bank", 0)
            karma = economy_data.get("karma", 0)

            return inventory_data, pocket, bank, karma

        except Exception as e:
            if config.DEBUG:
                print(f"Error processing collection {collection_name}: {e}")
            return {}, 0, 0, 0  # Return defaults in case of an error

    async def list_leaderboard_pocket(self):
        collections = await self.db_users.list_collection_names()

        collection_totals = {}

        # Iterate through each collection to aggregate data
        for collection_name in collections:
            # No need to await this
            collection = self.db_users[collection_name]

            pipeline = [
                {"$match": {"economy.pocket": {"$exists": True}}},
                {"$group": {"_id": None, "total_pocket": {"$sum": "$economy.pocket"}}},
            ]

            # Execute the aggregation pipeline on the collection
            try:
                cursor = collection.aggregate(pipeline)
                result = await cursor.to_list(length=1)
                if result and "total_pocket" in result[0]:
                    collection_totals[collection_name] = result[0]["total_pocket"]

            except Exception as e:
                if config.DEBUG:
                    print(f"Error processing collection {collection_name}: {e}")

        # Sort collections by total_pocket in descending order and get the top 15
        sorted_collections = sorted(
            collection_totals.items(), key=lambda x: x[1], reverse=True
        )[:15]

        # Convert to dictionary with collection_name as the key and total_pocket value
        leaderboard = {
            collection_name: total_pocket
            for collection_name, total_pocket in sorted_collections
        }

        return leaderboard

    async def list_leaderboard_bank(self):
        collections = await self.db_users.list_collection_names()

        collection_totals = {}

        # Iterate through each collection to aggregate data
        for collection_name in collections:
            collection = self.db_users[collection_name]

            pipeline = [
                {"$match": {"economy.bank": {"$exists": True}}},
                {"$group": {"_id": None, "total_pocket": {"$sum": "$economy.bank"}}},
            ]

            # Execute the aggregation pipeline on the collection
            try:
                cursor = collection.aggregate(pipeline)
                result = await cursor.to_list(length=1)
                if result and "total_bank" in result[0]:
                    collection_totals[collection_name] = result[0]["total_bank"]

            except Exception as e:
                if config.DEBUG:
                    print(f"Error processing collection {collection_name}: {e}")

        # Sort collections by total_bank in descending order and get the top 15
        sorted_collections = sorted(
            collection_totals.items(), key=lambda x: x[1], reverse=True
        )[:15]

        # Convert to dictionary with collection_name as the key and total_pocket value
        leaderboard = {
            collection_name: total_bank
            for collection_name, total_bank in sorted_collections
        }

        return leaderboard

    async def inc_user_comm_count(self, user_id):
        collection_name = str(user_id)

        try:
            update_result = await self.db_users[collection_name].update_one(
                {}, {"$inc": {"commands": 1}}, upsert=True
            )

            return update_result.modified_count
        except Exception as e:
            if config.DEBUG:
                print(f"Error updating commands: {e}")
            return None

    async def get_user_comm_count(self, user_id):
        collection_name = str(user_id)
        try:
            data = await self.db_users[collection_name].find_one({}, {"commands": 0})
            return data.get("commands", 0) if data else 0
        except Exception as e:
            if config.DEBUG:
                print(f"Error retrieving command count for user {user_id}: {e}")
            return 0

    async def inc_guild_comm_count(self, guild_id):
        collection_name = str(guild_id)

        try:
            update_result = await self.db_guilds[collection_name].update_one(
                {}, {"$inc": {"commands": 1}}, upsert=True
            )

            return update_result.modified_count
        except Exception as e:
            if config.DEBUG:
                print(f"Error updating commands: {e}")
            return None

    async def get_guild_comm_count(self, guild_id):
        collection_name = str(guild_id)
        try:
            data = await self.db_guilds[collection_name].find_one({}, {"commands": 0})
            return data.get("commands", 0) if data else 0
        except Exception as e:
            if config.DEBUG:
                print(f"Error retrieving command count for guild {guild_id}: {e}")
            return 0

    async def com_count_total(self):
        total_count = 0

        # List all collections in the db_guilds database
        collection_names = await self.db_guilds.list_collection_names()

        # Iterate over each collection
        for collection_name in collection_names:
            # Check if any document has the 'commands' field in the current collection
            result_check = await self.db_guilds[collection_name].find_one(
                {"commands": {"$exists": True}}
            )
            if not result_check:
                continue

            # Define the aggregation pipeline
            pipeline = [
                {"$match": {"commands": {"$exists": True}}},
                {
                    "$project": {
                        "commands_values": {
                            "$cond": {
                                "if": {"$eq": [{"$type": "$commands"}, "object"]},
                                "then": {"$objectToArray": "$commands"},
                                "else": [{"k": "total", "v": "$commands"}],
                            }
                        }
                    }
                },
                {"$unwind": "$commands_values"},
                {
                    "$group": {
                        "_id": None,
                        "total_count": {"$sum": "$commands_values.v"},
                    }
                },
            ]

            # Execute the aggregation pipeline
            try:
                cursor = self.db_guilds[collection_name].aggregate(pipeline)
                async for doc in cursor:
                    total_count += doc.get("total_count", 0)
            except Exception as e:
                if config.DEBUG:
                    print(
                        f"Error during aggregation for collection {collection_name}: {e}"
                    )

        return total_count

    async def set_ticket_info(self, guild_id, category_id=None, role_id=None):
        collection_name = str(guild_id)
        try:
            update_query = {}

            if category_id is not None:
                update_query["$set"] = {"ticket.category": category_id}

            if role_id is not None:
                update_query["$set"] = {"ticket.role": role_id}

            if "$set" in update_query:
                await self.db_guilds[collection_name].update_one(
                    {},
                    update_query,
                    upsert=True,
                )
                return True
            else:
                if config.DEBUG:
                    print(f"No valid data to update for guild {guild_id}.")
                return False

        except Exception as e:
            if config.DEBUG:
                print(f"Error setting ticket info in guild {guild_id}: {e}")
            return False

    async def get_ticket_info(self, guild_id):
        collection_name = str(guild_id)
        try:
            document = await self.db_guilds[collection_name].find_one({})
            if document:
                category_id = document.get("ticket", {}).get("category")
                role_id = document.get("ticket", {}).get("role")
                return category_id, role_id
            else:
                if config.DEBUG:
                    print(f"No ticket info found for guild {guild_id}.")
                return None, None
        except Exception as e:
            if config.DEBUG:
                print(f"Error retrieving ticket info for guild {guild_id}: {e}")
            return None, None

    async def add_warning(self, guild_id, user_id, moderator, reason):
        collection_name = str(guild_id)
        try:
            new_entry = {"moderator": moderator, "reason": reason}

            # Update the user's collection by adding the new warning to the 'warning' array
            await self.db_guilds[collection_name].update_one(
                {"user_id": user_id},
                {"$push": {"warning": new_entry}},
                upsert=True,
            )
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error adding warning for user {user_id}: {e}")
            return False

    async def remove_warning(self, guild_id, user_id, position):
        collection_name = str(guild_id)
        try:
            user_document = await self.db_guilds[collection_name].find_one(
                {"user_id": user_id}
            )

            if user_document and "warning" in user_document:
                warnings = user_document["warning"]
                if 0 < position <= len(warnings):
                    # Convert the 1-based position to 0-based index
                    index = position - 1

                    # Remove the warning at the identified index
                    await self.db_guilds[collection_name].update_one(
                        {"user_id": user_id}, {"$unset": {f"warning.{index}": ""}}
                    )

                    # Clean up the array after removal
                    await self.db_guilds[collection_name].update_one(
                        {"user_id": user_id}, {"$pull": {"warning": None}}
                    )

                    return True

            return False

        except Exception as e:
            if config.DEBUG:
                print(f"Error removing warning for user {user_id}: {e}")
            return False  # Return False if update fails

    async def list_warning(self, guild_id, user_id):
        collection_name = str(guild_id)
        try:
            # Get the document for the user
            user_document = await self.db_guilds[collection_name].find_one(
                {"user_id": user_id}
            )

            if user_document and "warning" in user_document:
                return user_document["warning"]
            else:
                return []
        except Exception as e:
            print(f"Error getting warning list for user {user_id}: {e}")
            return []

    async def set_afk(self, user_id, reason, time):
        collection_name = str(user_id)
        try:
            # Update the user's collection by adding the new warning to the 'warning' array
            await self.db_users[collection_name].update_one(
                {},
                {"$set": {"afk": {"reason": reason, "time": time}}},
                upsert=True,
            )
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error setting afk status for user {user_id}: {e}")
            return False

    async def remove_afk(self, user_id):
        collection_name = str(user_id)
        try:
            # Remove the AFK status for the user
            await self.db_users[collection_name].update_one({}, {"$unset": {"afk": ""}})
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error removing afk status for user {user_id}: {e}")
            return False

    async def get_afk(self, user_id):
        collection_name = str(user_id)
        try:
            # Get the AFK status for the user
            user_document = await self.db_users[collection_name].find_one(
                {}, {"afk": 1, "_id": 0}
            )
            return user_document.get("afk", None)
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting afk status for user {user_id}: {e}")
            return None

    async def set_suggestion(self, guild_id, channel_id):
        collection_name = str(guild_id)
        try:
            # Update the suggestion channel in the database
            result = await self.db_guilds[collection_name].update_one(
                {}, {"$set": {"suggestion": channel_id}}, upsert=True
            )
            return True

        except Exception as e:
            if config.DEBUG:
                print(f"Error setting suggestions channel for guild {guild_id}: {e}")
            return False

    async def get_suggestion(self, guild_id):
        collection_name = str(guild_id)
        try:
            document = await self.db_guilds[collection_name].find_one({})
            if document and "suggestion" in document:
                return document["suggestion"]
            return None
        except Exception as e:
            if config.DEBUG:
                print(f"Error retrieving suggestion channel for guild {guild_id}: {e}")
            return None

    async def remove_suggestion(self, guild_id):
        collection_name = str(guild_id)
        try:
            # Use an appropriate query to remove the suggestion data
            result = await self.db_guilds[collection_name].update_one(
                {}, {"$unset": {"suggestion": ""}}
            )
            if result.modified_count > 0:
                return True
            else:
                if config.DEBUG:
                    print(
                        f"No suggestion channel found to remove for guild {guild_id}."
                    )
                return False  # Return False if no documents were modified
        except Exception as e:
            if config.DEBUG:
                print(f"Error removing suggestion channel from guild {guild_id}: {e}")
            return False

    async def chatbot_set(self, guild_id, channel_id):
        collection_name = str(guild_id)
        try:
            # Convert channel_id to an integer
            channel_id = int(channel_id)

            await self.db_guilds[collection_name].update_one(
                {},
                {"$set": {"chatbot": channel_id}},
                upsert=True,
            )
            return True
        except Exception as e:
            if config.DEBUG:
                print(
                    f"Error setting chatbot channel in guild {guild_id} to channel {channel_id}: {e}"
                )
            return False

    async def chatbot_get(self, guild_id):
        collection_name = str(guild_id)
        try:
            document = await self.db_guilds[collection_name].find_one({})
            if document and "chatbot" in document:
                return int(document["chatbot"])
            return None
        except Exception as e:
            print(f"Error retrieving chatbot data for guild {guild_id}: {e}")
            return None

    async def chatbot_remove(self, guild_id):
        collection_name = str(guild_id)
        try:
            result = await self.db_guilds[collection_name].update_one(
                {}, {"$unset": {"chatbot": ""}}
            )
            if result.modified_count > 0:
                return True
            else:
                if config.DEBUG:
                    print(f"No chatbot data found to remove for guild {guild_id}.")
                return False
        except Exception as e:
            if config.DEBUG:
                print(f"Error removing chatbot data from {guild_id}: {e}")
            return False

    async def db_get(self, dbtype, collection, entry):
        """
        Get data from the database based on the dbtype, collection, and entry.

        :param dbtype: Type of the database (1 for users, 2 for guilds).
        :param collection: The name of the collection within the database.
        :param entry: The path to the data within the document.
        :return: A tuple (success, data) where success is a boolean and data is the fetched data or an empty dict on failure.
        """
        try:
            # Choose the database collection based on dbtype
            if dbtype == 1:
                database = self.db_users
            elif dbtype == 2:
                database = self.db_guilds
            else:
                raise ValueError("Invalid dbtype provided.")

            # Fetch the document by ID
            document = await database[collection].find_one({})
            if not document:
                return False, {"error": "Document not found"}

            # Extract the data based on the entry path
            keys = entry.split(".")
            data = document
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key, {})
                else:
                    return False, {"error": "Invalid path in the document"}

            return True, data

        except Exception as e:
            if config.DEBUG:
                print(f"Error getting data: {e}")
            return False, {"error": str(e)}

    # TODO add when float or int set the correct value type
    async def db_set(self, dbtype, collection, path, value):
        """
        Set a value in the database based on the dbtype, collection, path, and value.

        :param dbtype: Type of the database (1 for users, 2 for guilds).
        :param collection: The name of the collection within the database.
        :param path: The path to the data within the document.
        :param value: The value to set in the document.
        :return: A tuple (success, old_value) where success is a boolean and old_value is the previous value or an error message.
        """
        try:
            # Choose the database collection based on dbtype
            if dbtype == 1:
                database = self.db_users
            elif dbtype == 2:
                database = self.db_guilds
            else:
                raise ValueError("Invalid dbtype provided.")

            # Fetch the existing document
            document = await database[collection].find_one({})
            if not document:
                return False, "Document not found"

            # Extract the current value based on the path
            keys = path.split(".")
            current_data = document
            for key in keys[:-1]:
                if isinstance(current_data, dict):
                    current_data = current_data.get(key, {})
                else:
                    return False, "Invalid path in the document"

            old_value = current_data.get(keys[-1], None)

            # Update the document with the new value
            update_result = await database[collection].update_many(
                {}, {"$set": {path: value}}  # Update all documents
            )

            if update_result.modified_count > 0:
                return True, old_value
            else:
                return False, "No documents updated"

        except Exception as e:
            if config.DEBUG:
                print(f"Error setting data: {e}")
            return False, str(e)

    async def stocks_buy(self, user_id, symbol, shares, amount, price):
        collection_name = str(user_id)

        datetime.utcnow()
        timestamp = int(datetime.now().timestamp())

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"stocks": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Deduct money from user's bank
                    result = await self.db_users[collection_name].update_one(
                        # Ensure user has enough money
                        {"economy.bank": {"$gte": amount}},
                        {"$inc": {"economy.bank": -amount}},
                        session=session,
                    )

                    # Check if the deduction was successful
                    if result.matched_count == 0:
                        await session.abort_transaction()
                        if config.DEBUG:
                            print(
                                f"Error: User {user_id} does not have enough in their bank."
                            )
                        return False, False

                    await self.db_users[collection_name].update_one(
                        {},
                        {
                            "$push": {
                                f"stocks.{symbol}.transactions": {
                                    "action": "buy",
                                    "shares": shares,
                                    "price": price,
                                    "timestamp": timestamp,
                                }
                            },
                            "$inc": {f"stocks.{symbol}.shares": shares},
                        },
                        upsert=True,
                        session=session,
                    )

                    await session.commit_transaction()

                    return True, True

                except Exception as e:
                    await session.abort_transaction()
                    if config.DEBUG:
                        print(f"Error buying stock {symbol} for user {user_id}: {e}")
                    return False, False

    async def stocks_sell(self, user_id, symbol, shares, amount, price):
        collection_name = str(user_id)

        datetime.utcnow()
        timestamp = int(datetime.now().timestamp())

        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"stocks": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If user does not exist, run the upsert function
            await self.upsert_economy(user_id)

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Add transaction and decuct shares user's stocks
                    result = await self.db_users[collection_name].update_one(
                        {},
                        {
                            "$push": {
                                f"stocks.{symbol}.transactions": {
                                    "action": "sell",
                                    "shares": shares,
                                    "price": price,
                                    "timestamp": timestamp,
                                }
                            },
                            "$inc": {f"stocks.{symbol}.shares": -shares},
                        },
                        upsert=True,
                        session=session,
                    )

                    # Check if the deduction was successful
                    if result.matched_count == 0:
                        await session.abort_transaction()
                        print(f"Error: User {user_id} does not have enough stocks.")
                        return False, False

                    # Add amount to user's bank
                    await self.db_users[collection_name].update_one(
                        {},
                        {"$inc": {"economy.bank": amount}},
                        upsert=True,
                        session=session,
                    )

                    await session.commit_transaction()

                    return True, True

                except Exception as e:
                    if config.DEBUG:
                        print(f"Error selling stock {stock} for user {user_id}: {e}")
                    return False, False

    async def stocks_portfolio(self, user_id):
        collection_name = str(user_id)

        # Check if the user exists and has stocks
        user_exists = (
            await self.db_users.db_users[collection_name].count_documents(
                {"stocks": {"$exists": True}}
            )
            > 0
        )

        if not user_exists:
            # If the user doesn't exist, run the upsert function
            await self.upsert_economy(user_id)

        try:
            # Query the database for stock data
            user_data = await self.db_users[collection_name].find_one({}, {"stocks": 1})

            if not user_data or "stocks" not in user_data:
                return {}, 0, 0

            # Fetch the user's stock data
            if not user_data or "stocks" not in user_data:
                return {}  # Return empty data if no stocks exist

            # Fetch the user's stock data
            stocks_data = user_data["stocks"]
            portfolio = {}

            for symbol, data in stocks_data.items():
                transactions = data["transactions"]
                total_shares = 0
                total_cost = 0

                # Process each transaction for the current stock symbol
                for txn in transactions:
                    if txn["action"] == "buy":
                        total_shares += txn["shares"]
                        total_cost += txn["shares"] * txn["price"]
                    elif txn["action"] == "sell":
                        total_shares -= txn["shares"]
                        total_cost -= txn["shares"] * txn["price"]

                # Save processed data for the stock in the portfolio dictionary
                portfolio[symbol] = {
                    "shares": total_shares,
                    "total_cost": total_cost,
                    "transactions": transactions,  # You can choose to keep transactions if needed
                }

            return portfolio  # Ensure portfolio is returned as a dictionary
            portfolio = {}

            for symbol, data in stocks_data.items():
                transactions = data["transactions"]
                total_shares = 0
                total_cost = 0

                # Process each transaction for the current stock symbol
                for txn in transactions:
                    if txn["action"] == "buy":
                        total_shares += txn["shares"]
                        total_cost += txn["shares"] * txn["price"]
                    elif txn["action"] == "sell":
                        total_shares -= txn["shares"]
                        total_cost -= txn["shares"] * txn["price"]

                # Save processed data for the stock in the portfolio dictionary
                portfolio[symbol] = {
                    "shares": total_shares,
                    "total_cost": total_cost,
                    "transactions": transactions,  # You can choose to keep transactions if needed
                }

            return portfolio  # Ensure portfolio is returned as a dictionary

        except Exception as e:
            if config.DEBUG:
                print(f"Error processing collection {collection_name}: {e}")
            return {}  # Return empty data in case of an error

    async def stocks_leaderboard(self):
        collections = await self.db_users.list_collection_names()

        collection_totals = {}

        # Iterate through each collection to aggregate stock values
        for collection_name in collections:
            try:
                collection = self.db_users[collection_name]
                pipeline = [
                    {"$match": {"stocks": {"$exists": True}}},
                    {
                        "$project": {
                            "stocks_total": {
                                "$sum": {
                                    "$map": {
                                        "input": {"$objectToArray": "$stocks"},
                                        "as": "stock",
                                        "in": {"$multiply": ["$$stock.v", 1]},
                                    },
                                },
                            },
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total_stocks": {"$sum": "$stocks_total"},
                        }
                    },
                ]

                # Execute the aggregation pipeline
                cursor = collection.aggregate(pipeline)
                result = await cursor.to_list(length=1)
                if result:
                    collection_totals[collection_name] = result[0].get(
                        "total_stocks", 0
                    )

            except Exception as e:
                if config.DEBUG:
                    print(f"Error processing collection {collection_name}: {e}")

        # Sort collections by total stock value in descending order and get the top 15
        sorted_collections = sorted(
            collection_totals.items(), key=lambda x: x[1], reverse=True
        )[:15]

        # Convert to a leaderboard dictionary
        leaderboard = {
            collection_name: total_value
            for collection_name, total_value in sorted_collections
        }

        return leaderboard
