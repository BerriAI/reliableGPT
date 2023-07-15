import redis
import requests

from reliablegpt.constants import DEFAULT_INSTANCE_ID
from reliablegpt.settings import settings


class BaseCache:
    def put(self, input_prompt, response, *args, **kwargs):
        raise NotImplementedError

    def get(self, input_prompt, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def map_results(extracted_result) -> dict:
        return {"choices": [{"message": {"content": extracted_result}}]}


class DefaultCache(BaseCache):
    """1st iteration of refactor, this still needs lots of improvements."""

    def put(self, input_prompt, response, *args, **kwargs):
        request, user_email, customer_id = kwargs["request"], kwargs["user_email"], kwargs["customer_id"]
        url = "https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/add_cache"
        querystring = {
            "customer_id": customer_id,
            "instance_id": request.args.get("instance_id") or DEFAULT_INSTANCE_ID,
            "user_email": user_email,
            "input_prompt": input_prompt,
            "response": response,
        }
        requests.post(url, params=querystring)

    def get(self, input_prompt, *args, **kwargs) -> dict:
        request, user_email, customer_id = kwargs["request"], kwargs["user_email"], kwargs["customer_id"]
        url = "https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/get_cache"
        querystring = {
            "customer_id": customer_id,
            "instance_id": request.args.get("instance_id") or DEFAULT_INSTANCE_ID,
            "user_email": user_email,
            "input_prompt": input_prompt,
        }
        response = requests.get(url, params=querystring)
        print(f"cached response: {response.json()}")  # todo: PROPER LOGGING
        extracted_result = response.json()["response"]
        return self.map_results(extracted_result=extracted_result)


class RedisCache(BaseCache):
    """For now, we do the simplest approach possible, meaning we cache the results in Redis. Using exact match
    strategy. In the future this should be extended to other stores and similarity based matching to enable
    true semantic caching. For that vector store handling needs to be added. Proper exception handling."""

    def __init__(self):
        self.cache = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True
        )

    def put(self, input_prompt, response, *args, **kwargs):
        self.cache.set(input_prompt, response)

    def get(self, input_prompt, *args, **kwargs):
        if self.cache.exists(input_prompt):
            return self.map_results(extracted_result=self.cache.get(input_prompt))
