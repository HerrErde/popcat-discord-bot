import json

import requests

import config
from db import RedisHandler


class Voting:
    redis_client = None

    @classmethod
    async def init_redis(cls):
        if not cls.redis_client:
            cls.redis_client = await RedisHandler().get_client()

    @classmethod
    async def vote_get(cls, bot_id, user_id):
        if not cls.redis_client:
            await cls.init_redis()

        try:
            headers = {"Authorization": config.VOTING_KEY}
            url = f"https://top.gg/api/bots/{bot_id}/check?userId={user_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()  # Parse JSON response
            vote_count = data.get("voted", 0)
        except (requests.RequestException, json.JSONDecodeError):
            return None

        vote_key = f"{user_id}:voting:{vote_count}"

        save_vote = await self.redis_client.get(f"{user_id}:voting:*")
        if save_vote is not None:
            save_vote = int(save_vote)

        if vote_count == save_vote:
            return True, False, 0
        elif vote_count > save_vote:
            difference = vote_count - save_vote
            await self.redis_client.set(vote_key, vote_count)
            return True, True, difference
        else:
            await self.redis_client.set(vote_key, vote_count)
            return True, True, 0
