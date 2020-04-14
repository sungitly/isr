# -*- coding: utf-8 -*-
from application.redisstore import redis_store


class UserDevice(object):
    def __init__(self, user_id, type, token):
        self.user_id = user_id
        self.type = type
        self.token = token

    # type: set
    devices_tokens_users_key = 'isr:devices:tokens:users:%s'
    # type: hash
    devices_users_mapping_key = 'isr:devices:users:mapping'
    # type: set
    devices_tokens_android_key = 'isr:devices:tokens:android'
    # type: set
    devices_tokens_ios_key = 'isr:devices:tokens:ios'

    @staticmethod
    def add_device(device):
        existing_binding_user_id = UserDevice.get_binding_user_from_token(device.token)

        if existing_binding_user_id and existing_binding_user_id != device.user_id:
            UserDevice.del_device_token_for_user(device.token, existing_binding_user_id)

        redis_store.sadd(UserDevice.devices_tokens_users_key % device.user_id, device.token)
        redis_store.hset(UserDevice.devices_users_mapping_key, device.token, device.user_id)
        if device.type == 'ios':
            redis_store.sadd(UserDevice.devices_tokens_ios_key, device.token)
        elif device.type == 'android':
            redis_store.sadd(UserDevice.devices_tokens_android_key, device.token)

    @staticmethod
    def get_binding_user_from_token(token):
        return redis_store.hget(UserDevice.devices_users_mapping_key, token)

    @staticmethod
    def del_device_token_for_user(token, user_id):
        redis_store.srem(UserDevice.devices_tokens_android_key, token)
        redis_store.srem(UserDevice.devices_tokens_ios_key, token)
        return redis_store.srem(UserDevice.devices_tokens_users_key % user_id, token)

    @staticmethod
    def get_all_device_tokens_for_user(user_id):
        return redis_store.smembers(UserDevice.devices_tokens_users_key % user_id)

    @staticmethod
    def del_device_tokens_for_user(user_id):
        tokens = UserDevice.get_all_device_tokens_for_user(user_id)

        for token in tokens:
            UserDevice.del_device_token_for_user(token, user_id)

    @staticmethod
    def get_device_type_by_token(token):
        if redis_store.sismember(UserDevice.devices_tokens_ios_key, token):
            return 'ios'
        else:
            return 'android'
