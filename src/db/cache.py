import asyncio

import redis.asyncio as redis

import config

redis_host = config.REDIS_HOST
redis_port = config.REDIS_PORT
redis_user = config.REDIS_USER
redis_pass = config.REDIS_PASS

REDIS_URI = f"redis://{redis_user}:{redis_pass}@{redis_host}:{redis_port}"


class RedisHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self, max_retries=5, retry_delay=2):
        if self._initialized:
            return  # Already initialized, so do nothing

        for attempt in range(max_retries):
            try:
                self.REDIS_URI = (
                    f"redis://{redis_user}:{redis_pass}@{redis_host}:{redis_port}"
                )
                self.redis_client = await redis.from_url(
                    self.REDIS_URI, socket_timeout=5
                )

                # Test connection
                await self.redis_client.ping()
                print("Successfully connected to Redis")
                self._initialized = True
                return
            except (redis.ConnectionError, redis.TimeoutError) as e:
                print(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    print("Max retries reached. Failed to connect to Redis.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break

    async def get_client(self):
        if not self._initialized:
            await self.initialize()
        return self.redis_client
