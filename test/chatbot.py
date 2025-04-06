import json
from langchain.chains import LLMChain
from langchain_huggingface import HuggingFaceEndpoint
from db import RedisHandler


class Chatbot:
    def __init__(self):
        self.redis_client = None

    async def init_redis(self):
        self.redis_client = await RedisHandler().get_client()

    async def save_message_history(self, chat_id, user_message, bot_response):
        message_history = {"user_message": user_message, "bot_response": bot_response}
        await self.redis_client.rpush(chat_id, json.dumps(message_history))

    def init_model(self, model_name="gpt-2"):
        self.llm = HuggingFaceEndpoint(model_name=model_name)
        self.chain = LLMChain(llm=self.llm, prompt="")

    async def chat(self, chat_id, user_message):
        await chatbot.init_redis()
        chatbot.init_model()
        response = self.chain.run(user_message)
        await self.save_message_history(chat_id, user_message, response)
        return response
