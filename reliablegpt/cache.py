import redis

from reliablegpt.settings import settings


class BaseCache:
    def put(self, key, value):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError


class RedisCache(BaseCache):
    """For now, we do the simplest approach possible, meaning we cache the results in Redis. Using exact match
    strategy. In the future this should be extended to other stores and similarity based matching to enable
    true semantic caching. For that vector store handling needs to be added. Proper exception handling."""

    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True
        )

    def put(self, key, value):
        self.redis.set(key, value)

    def get(self, key):
        return self.redis.get(key)
