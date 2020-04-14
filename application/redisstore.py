# -*- coding: utf-8 -*-
import redis
from config import Config

redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, password=Config.REDIS_PASSWORD, db=1)
stats_redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, password=Config.REDIS_PASSWORD,
                                      db=4)
int_redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, password=Config.REDIS_PASSWORD,
                                    db=5)
