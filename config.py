# -*- coding: utf-8 -*-
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from urlparse import urlparse

from flask import request

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
base_dir = os.path.dirname(__file__)


class Config(object):
    def __init__(self):
        pass

    MODE = ''
    VERSION = '1.3.19'

    logging.basicConfig(format=LOG_FORMAT)
    config_logger = logging.getLogger(__name__)

    # project config
    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    LOG_FOLDER = os.path.join(PROJECT_ROOT, 'isr', 'logs')
    DATA_FOLDER = os.path.join(PROJECT_ROOT, 'isr', 'migrations', 'data')
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'isr', 'uploads')
    INV_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'inv')
    AUTH_SERVER_URL = 'http://120.27.42.196'
    RADAR_SERVER_URL = 'http://115.28.191.78'
    with open(os.path.join(base_dir, 'package.json')) as data_file:
        package_json = json.load(data_file)
    ASSETS_VERSION_PATH = package_json['version'] + '/'

    ALLOWED_EXTENSIONS = ['xlsx', 'png', 'jpg', 'jpeg']

    SECRET_KEY = "4fd9fc0a5e668d3a4de0165a9998faab"
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 30 * 12
    SESSION_COOKIE_NAME = 'isr_session'

    from application.integration.params import TOKEN_UCENTER
    UCENTER_AUTH_TOKEN_KEY = TOKEN_UCENTER

    # database config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URI = os.environ.get('REDIS_URL')

    REDIS_HOST = 'localhost'
    REDIS_PORT = '6379'
    REDIS_PASSWORD = ''

    RADAR_DATA_URL = 'http://115.28.191.78/'

    try:
        parsed_redis_url = urlparse(REDIS_URI)
        if parsed_redis_url and parsed_redis_url.scheme == 'redis':
            REDIS_HOST = parsed_redis_url.hostname
            REDIS_PORT = parsed_redis_url.port
            REDIS_PASSWORD = parsed_redis_url.password
    except:
        config_logger.warning(
            'REDIS_URL env variable is not available. Use default settings ' + 'redis://' + REDIS_HOST + ':' + REDIS_PORT)

    # flask config
    TRAP_HTTP_EXCEPTIONS = True
    TRAP_BAD_REQUEST_ERRORS = True

    # flask-babel config
    BABEL_DEFAULT_LOCALE = 'zh_CN'

    # flask-cache config
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = REDIS_HOST
    CACHE_REDIS_PORT = REDIS_PORT
    CACHE_REDIS_PASSWORD = REDIS_PASSWORD
    CACHE_KEY_PREFIX = 'isr:'
    CACHE_REDIS_DB = 2

    # Redis Usage Summary
    # db1 is used by isr app
    # db2 is used by isr app cache
    # db3 is used by celery
    # db4 is used by isr app stats

    # redis backend will replaced by rabbitmq very soon.
    CELERY_BROKER_URL = 'redis://:' + REDIS_PASSWORD + '@localhost:6379/3'
    CELERY_TASK_RESULT_EXPIRES = 1800

    # integration config
    HWJD_OA_SERVER = 'http://123.58.230.82/'

    FRT_WS_URL = 'http://218.83.161.55:8000/ERP_API/Service.svc'
    FRT_API_KEY = '57B9789F-86C3-4374-87DE-CBE95DA7BE46'
    FRT_DEMO = True

    def init_app(self, app):
        self.init_log(app)

        app.logger.debug('Application is initialed with %s', self.__class__.__name__)

    def init_log(cls, app):
        pass


class DevelopmentConfig(Config):
    MODE = 'development'
    DEFAULT = True

    DEBUG = True

    AUTH_SERVER_URL = 'http://127.0.0.1:5000'
    UCENTER_AUTH_SERVER_URL = 'http://127.0.0.1:5002'

    SQLALCHEMY_ECHO = True
    SQLALCHEMY_RECORD_QUERIES = True


class DebugConfig(Config):
    MODE = 'debug'

    def init_log(self, app):
        config_log(app, 'debug.log', logging.DEBUG)

    def init_app(self, app):
        super(DebugConfig, self).init_app(app)

        @app.before_request
        def log_request():
            app.logger.debug(
                u'\nIncoming Request: \n** Request Path **: %s \n** Request Header **:\n%s\n** Request Body **: %s\n' % (
                    request.path, headers_str(request),
                    unicode(request.data, 'utf-8')))

        def headers_str(request):
            header_str = ''
            for key, value in request.headers.items():
                header_str += '%s: %s\n' % (key, value)
            return header_str[:-1]


class TestConfig(DevelopmentConfig):
    MODE = 'test'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:welcome@localhost/isr_test'


class ProductionConfig(Config):
    MODE = 'production'

    UCENTER_AUTH_SERVER_URL = 'http://120.27.42.196:5001'

    def init_log(self, app):
        config_log(app, 'app.log', logging.WARNING)


def config_log(app, filename, level):
    # config app log
    if not os.path.exists(os.path.dirname(Config.LOG_FOLDER)):
        os.makedirs(os.path.dirname(Config.LOG_FOLDER))

    info_log = os.path.join(Config.LOG_FOLDER, filename)
    info_file_handler = RotatingFileHandler(info_log, maxBytes=10 * 1024 * 1024, backupCount=10)
    info_file_handler.setFormatter(
        logging.Formatter(LOG_FORMAT))
    info_file_handler.setLevel(level)

    app.logger.setLevel(level)
    app.logger.addHandler(info_file_handler)

    # config sqlalchemy log
    db_logger = logging.getLogger('sqlalchemy.engine')
    db_logger.setLevel(level)
    db_logger.addHandler(info_file_handler)


try:
    from config_local import *
except:
    pass

config = {}


def _scan():
    import sys
    cur_module = sys.modules[__name__]
    for item in dir(cur_module):
        if item[0].isupper():
            config_class = getattr(cur_module, item)
            if config_class is Config:
                continue
            if type(config_class) != type:
                continue
            if not issubclass(config_class, Config):
                continue
            if 'MODE' in config_class.__dict__:  # 使用自己的
                mode = getattr(config_class, 'MODE')
                config[mode] = config_class()
            if 'DEFAULT' in config_class.__dict__:  # 使用自己的
                default = getattr(config_class, 'DEFAULT')
                if default:
                    config['default'] = config_class()


_scan()
del _scan
