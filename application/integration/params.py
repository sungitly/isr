#coding: utf-8
from types import MethodType
import json
from jsonschema import ValidationError

from jsonschema.validators import Draft4Validator

TOKEN_UCENTER = 'xxxxxxxxxxx' #认证头的key


class AuthParamException(Exception):
    code = 1000
    message = ''
    '''
    认证参数错误
    '''
    def __init__(self, message, *args, **kwargs):
        super(AuthParamException, self).__init__(args, kwargs)
        self.message = message


class AuthBase(object):
    '''
    请求基类
    '''
    schema = {}
    @classmethod
    def from_data(cls, data):
        pass

    def to_data(self):
        pass

    def to_str(self):
        return json.dumps(self.to_data())


def _validate_schema(schema, instance):
    validator = Draft4Validator(schema)
    try:
        validator.validate(instance)
    except ValidationError as e:
        raise AuthParamException(str(e))


def _check_str(s):
    if not isinstance(s, (str, unicode)):
        raise AuthParamException('param must be string')
    s = s.strip()
    if s == '':
        raise AuthParamException('param must have value')
    return s


def _check_int(i):
    if not isinstance(i, (int, long)):
        raise AuthParamException('param must be int')
    return i


#######################请求数据#############

class AuthLoginRequest(AuthBase):
    '''
    user_login 请求参数
    '''
    schema = {
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'ip': {'type': 'string'},
            'device': {'type':'string'}
        },
        'required': ['username', 'password']
    }

    def __init__(self, username, password):

        self.username = _check_str(username)
        self.password = _check_str(password)

    @classmethod
    def from_data(cls, data):
        _validate_schema(cls.schema, data)
        return cls(data['username'],
                   data['password'])

    def to_data(self):
        return {
            'username': self.username,
            'password': self.password
        }


class AuthChangePasswordRequest(AuthBase):
    '''
    user_changepassword请求参数
    '''
    schema = {
        'type': 'object',
        'properties': {
            'user_id': {'type': 'integer'},
            'old_password': {'type': 'string'},
            'new_password': {'type': 'string'},
            'ip': {'type': 'string'},
            'device': {'type':'string'}
        },
        'required': ['user_id', 'old_password', 'new_password']
    }

    def __init__(self, user_id, old_password, new_password):
        self.user_id = _check_int(user_id)
        self.old_password = _check_str(old_password)
        self.new_password = _check_str(new_password)

    @classmethod
    def from_data(cls, data):
        _validate_schema(cls.schema, data)
        return cls(data['user_id'],
                   data['old_password'],
                   data['new_password'])

    def to_data(self):
        return {
            'user_id': self.user_id,
            'old_password': self.old_password,
            'new_password': self.new_password
        }


user_ids_schema = {
    'type': 'string'
}


store_schema = {
    'type': 'object',
    'properties': {
        'id': {'type': 'integer'},
        'sequence_id': {'type': 'string'},
        'name': {'type': 'string'}
    },
    'required': ['id', 'name']
}


role_schema = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string'}
    },
    'required': ['title']
}


user_profile_schema = {
    'type': 'object',
    'properties': {
        'first_name': {'type': 'string'},
        'last_name': {'type': 'string'},
        'gender': {'type': 'integer'},
        'nick_name': {'type': 'string'},
        'QQ': {'type': 'string'},
        'title': {'type': 'string'},
        'avatar': {'type': 'string'},
    }
}


user_schema = {
    'type': 'object',
    'properties': {
        'id': {'type': 'integer'},
        'username': {'type':'string'},
        'last_login_on': {'type': 'string'},
        'status': {'type': 'string'},
        'qq_open_id': {'type': 'string'},
        'weibo_open_id': {'type': 'string'},
        'webchat_open_id': {'type': 'string'},
        'email': {'type': 'string'},
        'mobile': {'type': 'string'},
        'profile': user_profile_schema
    },
    'required': ['id', 'username']
}


scope_type_schema = {
    'enum': ['individual', 'store', 'peoples']
}


class AuthUserInfosRequest(AuthBase):
    schema = user_ids_schema
    def __init__(self, user_ids):
        self.user_ids = user_ids

    @classmethod
    def from_data(cls, data):
        _validate_schema(cls.schema, data)
        return cls(data)

    def to_param(self): #get请求方式
        return '&'.join(['uid=%d' % uid for uid in self.user_ids])


############### ucenter 返回数据########

class AuthLoginResponse(AuthBase):
    '''
    user_login 返回数据
    '''
    schema = {
        'type': 'object',
        'properties': {
            'user': user_profile_schema,
            'store_user_role_scopes': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'store': store_schema,
                        'role': role_schema,
                        'scope_type': scope_type_schema,
                        'user_ids': user_ids_schema
                    }
                }
            }
        },
        'required': ['user', 'store_user_role_scopes']
    }

    def __init__(self, user, store_user_role_scopes):
        self.user = user
        self.store_user_role_scopes = store_user_role_scopes

    @classmethod
    def from_data(cls, data):
        _validate_schema(cls.schema, data)
        return cls(data['user'], data['store_user_role_scopes'])

    def to_data(self):
        return {
            'user': self.user,
            'store_user_role_scopes': self.store_user_role_scopes
        }


class AuthUserInfoResponse(AuthBase):
    schema = {
        'type': 'array',
        'items': AuthLoginResponse.schema
    }

    def __init__(self, user_infos):
        self.user_infos = user_infos

    @classmethod
    def from_login_response_list(cls, lst):
        return cls([item.to_data() for item in lst])

    @classmethod
    def from_data(cls, lst):
        _validate_schema(cls.schema, lst)
        return cls(lst)

    def to_data(self):
        return self.user_infos

# class AuthChangePasswordResponse(AuthBase):
#     '''
#     user_changepassword 返回参数
#     '''
#     def __init__(self):
#         pass
#
#     @classmethod
#     def from_dict(cls, data):
#         pass
#
#     def to_dict(self):
#         return

############## 请求获取短信校验


class RestoreGetChecksumRequest(AuthBase):
    '''
    获取用户密码重置code
    '''
    schema = {
        'type': 'object',
        'properties': {
            'mobile': {'type': 'string'}
        },
        'required': ['mobile']
    }

    def __init__(self, mobile):
        self.mobile = mobile

    @classmethod
    def from_data(cls, data):
        _validate_schema(cls.schema, data)
        return cls(data['mobile'])

    def to_data(self):
        return {
            'mobile': self.mobile
        }


class RestoreGetChecksumResponse(AuthBase):
    '''
    返回token
    '''
    schema = {
        'type': 'object',
        'properties': {
            'token': {'type': 'string'}
        },
        'required': ['token']
    }

    def __init__(self, token):
        self.token = token

    @classmethod
    def from_data(cls, data):
        _validate_schema(cls.schema, data)
        return cls(data['token'])

    def to_data(self):
        return {
            'token': self.token
        }


################ 请求重置密码

class RestorePasswordRequest(AuthBase):
    '''
    重置用户密码
    '''
    schema = {
        'type': 'object',
        'properties': {
            'token': {'type': 'string'},
            'checksum': {'type': 'string'},
            'password': {'type': 'string'},
            'device': {'type': 'string'},
            'ip': {'type': 'string'},
            'extra_data': {'type': 'string'}
        },
        'required': ['token', 'checksum', 'password']
    }

    def __init__(self, token, checksum, password, device=None, ip=None, extra_data=None):
        self.token = token
        self.checksum = checksum
        self.password = password
        self.ip = ip
        self.device = device
        self.extra_data = extra_data

    @classmethod
    def from_data(cls, data):
        _validate_schema(cls.schema, data)
        device = data.get('device', None)
        ip = data.get('ip', None)
        extra_data = data.get('extra_data', None)
        return cls(
            data['token'],
            data['checksum'],
            data['password'],
            device,
            ip,
            extra_data
        )

    def to_data(self):
        data = {
            'token': self.token,
            'checksum': self.checksum,
            'password': self.password,
            'device': self.device
        }
        if self.device:
            data.update({'device': self.device})
        if self.ip:
            data.update({'ip': self.ip})
        if self.extra_data:
            data.update({'extra_data': self.extra_data})
        return data
