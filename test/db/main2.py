import config
from db.mongodb import MongoDBHandler


class DBHandler:
    HANDLER_MAP = {
        "mongodb": MongoDBHandler,
    }

    def __init__(self):
        self.database_type = config.DATABASE_TYPE
        self.connection = self.get_handler()

    def get_handler(self):
        handler_class = self.HANDLER_MAP.get(self.database_type)
        if handler_class:
            return handler_class()  # Instantiate the handler class
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

    def add_customcommand(self, guild_id, trigger, response):
        try:
            # Ensure connection is properly initialized and of the correct type
            if isinstance(self.connection, MongoDBHandler):
                return Mongodb_handler.add_customcommand(guild_id, trigger, response)
            else:
                raise AttributeError(
                    f"Handler instance is not of type Mongodb_handler."
                )
        except Exception as e:
            print(f"Error adding custom command: {e}")
