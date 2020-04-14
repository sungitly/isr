# coding: utf-8

import requests
from werkzeug.wrappers import Request, Response


class ProxyMiddleware(object):
    '''
    转发wsgi中间件
    '''

    def __init__(self, app, token, url_map):
        self.app = app
        self.token = token
        self.url_map = url_map

    def __call__(self, environ, start_response):
        request = Request(environ)
        path = request.path
        method = request.method
        if (method, path) in self.url_map:
            url = self.url_map[(method, path)]
            fn = getattr(requests, method.lower())
            if fn:
                headers = request.headers
                headers_dict = dict(headers)
                headers_dict['x-forwarded-for'] = request.remote_addr
                res = fn(url=url + '?' + request.query_string, headers=headers_dict, data=request.data,
                         auth=(self.token, ''))
                res_headers = res.headers
                ignore_header = ['content-encoding', 'content-length']
                response_headers = [(k, res_headers[k]) for k in res_headers if
                                    not isinstance(k, (str, unicode)) or k.lower() not in ignore_header]
                res = Response(res.content, res.status_code, response_headers)
                return res(environ, start_response)
        return self.app(environ, start_response)
