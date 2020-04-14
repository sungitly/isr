# -*- coding: utf-8 -*-
from application.exceptions import (BizException,
                                    ValidationException,
                                    ServerException,
                                    is_json_exception)
from flask import jsonify, current_app, request, render_template
from werkzeug.exceptions import HTTPException


class ErrorHandler(object):
    def __init__(self, app):
        super(ErrorHandler, self).__init__()
        self.app = app

    def init_app(self, app):
        from application.api import api

        @app.errorhandler(ServerException)
        def handle_server_exception(error):
            if api.url_prefix in request.path  or is_json_exception(error):
                response = jsonify(
                    {'error': error.name, 'code': error.code, 'message': error.message, 'extras': error.extras})
                response.status_code = 500
                return response
            else:
                return render_template('site/errors.html', error_code=500)


        @app.errorhandler(HTTPException)
        def handle_http_exception(error):
            if api.url_prefix in request.path:
                response = jsonify({'error': error.name, 'message': error.description})
                response.status_code = error.code
                return response
            else:
                return render_template('site/errors.html', error_code=error.code)


        @app.errorhandler(BizException)
        def handle_biz_exception(error):
            if api.url_prefix in request.path or is_json_exception(error):
                if not error.message:
                    error.message = u'系统错误'
                response = jsonify(
                    {'error': error.name, 'code': error.code, 'message': error.message, 'extras': error.extras})
                response.status_code = 400
                return response
            else:
                return render_template('site/errors.html', error_code=400)

        @app.errorhandler(ValidationException)
        def handle_validation_exception(error):
            if api.url_prefix in request.path:
                response = jsonify({'error': {'errors': error.errors}, 'code': error.code, 'message': error.message})
                response.status_code = 400
                return response
            else:
                return render_template('site/errors.html', error_code=400)

        @app.errorhandler(Exception)
        def handle_general_exception(error):
            if api.url_prefix in request.path:
                display_msg = 'something has gone wrong' if current_app.config[
                                                                'MODE'] == 'production' else error.message
                response = jsonify({'error': type(error).__name__, 'message': display_msg})
                response.status_code = 500

                if hasattr(error, 'message'):
                    current_app.logger.exception('ISR ERRORS >>>>>>')
                return response
            else:
                return render_template('site/errors.html', error_code=500)
