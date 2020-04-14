# coding: utf-8
from flask import request

from . import api
from application.redisstore import redis_store
from application.integration.ucenter import uc_integration_get_token

CLIENT_NAME = 'insurance'


class IntegrationTokenCache(object):
    def __init__(self, redisClient):
        self.redisClient = redisClient

    @staticmethod
    def _gen_key(client_name, user_id):
        return 'INTEGRATION:%s:%s' % (client_name.upper(), user_id)

    def store(self, client_name, user_id, token, expire):
        key = self._gen_key(client_name, user_id)
        self.redisClient.setex(key, expire, token)

    def delete(self, client_name, user_id):
        key = self._gen_key(client_name, user_id)
        self.redisClient.delete(key)

    def query(self, client_name, user_id):
        key = self._gen_key(client_name, user_id)
        return self.redisClient.get(key)


@api.route('/insurance/gen_token/<int:user_id>')
def get_token(user_id):
    cache = IntegrationTokenCache(redis_store)

    def get_token():
        res_data = uc_integration_get_token(CLIENT_NAME, user_id=user_id)
        token = res_data['token']
        expires_in = res_data['expires_in']
        cache.store(CLIENT_NAME, user_id, token, expires_in)
        return token

    token = None
    if request.args.get('force'):
        token = get_token()
    else:
        data = cache.query(CLIENT_NAME, user_id)
        if not data:
            token = get_token()
        else:
            token = data
    return {'token': token}
