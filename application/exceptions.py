# -*- coding: utf-8 -*-
from application.utils import obj_to_dict


def is_json_exception(e):
    '''
    测试一个异常是否可以转化成json格式
    '''
    return getattr(e, 'json', False)


class ErrorDetail(object):
    def __init__(self, domain='', reason='', message=''):
        self.domain = domain
        self.reason = reason
        self.message = message

    def to_dict(self):
        return obj_to_dict(self)


class BizException(Exception):
    name = None
    code = None
    message = ''

    def __init__(self, message=None, **extras):
        if message:
            self.message = message
        self.extras = extras


class JsonExceptionMixIn():
    '''
    异常是否返回为json
    '''
    json = True


class ServerException(Exception):
    name = None
    code = None
    message = ''

    def __init__(self, message=None, **extras):
        if message:
            self.message = message
        self.extras = extras


class ValidationException(Exception):
    code = 100
    errors = []

    def __init__(self, errors=None, message=''):
        if errors:
            self.errors = [error.to_dict() for error in errors]
        self.message = message

    def append_error(self, error):
        self.errors.append(error.to_dict())


class InvalidMobileNumberExcetpion(BizException):
    name = "Invalid Mobile Number"
    code = 1000


class DuplicatedCustomerException(BizException):
    name = "Duplicated Customer"
    code = 1001


class NoPermissionOnCustomerException(BizException):
    name = "No Permission On Customer"
    code = 1002

    def __init__(self, customer, message):
        super(NoPermissionOnCustomerException, self).__init__(message)
        self.customer = customer


class IncorrectSalesAssignmentException(BizException):
    name = "Incorrect sales assignment"
    code = 1003


class InvalidSalesStatusTransitionException(BizException):
    name = "Invalid Sales Status Transition"
    code = 1004


class EmptyRequiredFields(BizException):
    name = "Please fill all required fields"
    code = 1005


class RestorePasswordOverflow(BizException, JsonExceptionMixIn):
    code = 2000
    name = "restore password too many times"
    message = u'重置请求次数过多'


class NeedMobileException(BizException, JsonExceptionMixIn):
    code = 2001
    name = 'need mobile'
    message = u'需要手机号码'


class InvalidateMobileException(BizException, JsonExceptionMixIn):
    code = 2002
    name = 'invalidate mobile'
    message = u'手机号码不合法'


class InvalidateCheckSum(BizException, JsonExceptionMixIn):
    code = 2003
    name = 'invalidate checksum'
    message = u'校验码异常'


class JsonRequestRequired(BizException, JsonExceptionMixIn):
    code = 2004
    name = 'need a json request'
    message = u'需要一个json请求'


class UserWasNotFound(BizException, JsonExceptionMixIn):
    code = 2005
    name = 'user was not found'
    message = u'用户未找到'


class UserWasNotAuthorized(BizException, JsonExceptionMixIn):
    code = 2006
    name = 'user was not authorized'
    message = u'用户密码错误'


class UserPasswordInvalid(BizException, JsonExceptionMixIn):
    code = 2007
    name = 'user password was invalidate'
    message = u'密码不合法'


class RestorePasswordInvalidToken(BizException, JsonExceptionMixIn):
    code = 2008
    name = 'invalidate token for restore password'
    message = u'重置密码的token异常'


class RestorePasswordChecksumMissmatch(BizException, JsonExceptionMixIn):
    code = 2009
    name = 'miss match checksum for restore password'
    message = u'重置用户密码的校验码不匹配'


class NewAppointmentDateWarningExcetpion(BizException):
    name = "new customer order appointment time later than 24 hours,confirm to submit?"
    message = u'首次预约客户预约时间大于24小时,确定要保存么?'
    code = 4001


class OldAppointmentDateWarningExcetpion(BizException):
    name = "old customer order appointment time later than 7 days,confirm to submit?"
    message = u'再次预约客户预约时间大于7天,确定要保存么?'
    code = 4002


class UCIntegrationNotFound(BizException):
    name = 'uc integration not found'
    message = u'ucenter 上不支持此服务'
    code = 4500


########  服务器异常

class UCenterConnectExcetion(ServerException):
    code = 3000
    name = 'Connection ucenter failed'
    message = u'连接ucenter服务器失败'


class UCenderConnectYunpianException(ServerException):
    code = 3001
    name = 'Connect yunpian Exception'
    message = u'ucenter服务器内部异常'


# FRT AUTO 集成异常
class FrtEncryptParamException(ServerException):
    code = 51001
    name = 'fail to encrypt params'
    message = u'参数不能被正确加密'


class FrtFetchStoreInventoriesException(ServerException):
    code = 51002
    name = 'fail to fetch store inventories'
    message = u'无法获取店面库存信息'


class FrtFetchSharedInventoriesException(ServerException):
    code = 51003
    name = 'fail to fetch shared inventories'
    message = u'无法获取共享库存信息'


class FrtFetchSharedInventoriesDetailsException(ServerException):
    code = 51004
    name = 'fail to fetch shared inventories details'
    message = u'无法获取共享库存详情信息'


class InvalidFrtInventoryLookupTypeException(BizException):
    code = 41001
    name = 'invalid frt lookup type'
    message = u'无效的Lookup类型'
