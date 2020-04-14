# -*- coding: utf-8 -*-
from string import zfill

from application.redisstore import redis_store


class SeqGen(object):
    sequence_gen_key = 'isr:seq:model:%s:store:%s'

    @staticmethod
    def generate_seq(model, store_id):
        if not model:
            model = 'unknown'

        if not store_id:
            store_id = 'unknown'

        name = SeqGen.sequence_gen_key % (model, store_id)

        return zfill(redis_store.incr(name), 8)
