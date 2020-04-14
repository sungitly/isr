# -*- coding: utf-8 -*-
from __future__ import division
from urllib import urlencode

from application.utils import convert_int

DEFAULT_PAGE_START = 1
DEFAULT_PAGE_SIZE = 20


# noinspection PyBroadException
def get_page_info(request):
    return get_page_info_from_dict(request.args)


def get_page_info_from_dict(data_dict):
    page = data_dict.get('page', DEFAULT_PAGE_START)
    page = convert_int(page, DEFAULT_PAGE_START)
    page = DEFAULT_PAGE_START if page < DEFAULT_PAGE_START else page

    per_page = data_dict.get('per_page', DEFAULT_PAGE_SIZE)
    per_page = convert_int(per_page, DEFAULT_PAGE_SIZE)

    return {"page": page, "per_page": per_page}


def page_slice(page, per_page):
    page = convert_int(page, DEFAULT_PAGE_START)
    per_page = convert_int(per_page, DEFAULT_PAGE_SIZE)

    return (page - 1) * per_page, page * per_page


def generate_header_link(request, pagination):
    params = dict()
    params.update(request.args)

    header_links = []
    if pagination.pages > 1 and pagination.has_prev:
        header_links.append(
            '<%s>; rel="first"' % build_url_with_new_params(request, {'page': DEFAULT_PAGE_START}))

    if pagination.has_prev:
        header_links.append('<%s>; rel="prev"' % build_url_with_new_params(request, {'page': pagination.prev_num}))

    if pagination.has_next:
        header_links.append('<%s>; rel="next"' % build_url_with_new_params(request, {'page': pagination.next_num}))

    if pagination.pages > 1 and pagination.has_next:
        header_links.append(
            '<%s>; rel="last"' % build_url_with_new_params(request, {'page': pagination.pages}))

    return ', '.join(header_links)


def encode_obj(in_obj):
    def encode_list(in_list):
        out_list = []
        for el in in_list:
            out_list.append(encode_obj(el))
        return out_list

    def encode_dict(in_dict):
        out_dict = {}
        for k, v in in_dict.iteritems():
            out_dict[k] = encode_obj(v)
        return out_dict

    if isinstance(in_obj, unicode):
        return in_obj.encode('utf-8')
    elif isinstance(in_obj, list):
        return encode_list(in_obj)
    elif isinstance(in_obj, tuple):
        return tuple(encode_list(in_obj))
    elif isinstance(in_obj, dict):
        return encode_dict(in_obj)

    return in_obj


def build_url_with_new_params(request, new_params):
    params = dict()
    params.update(request.args)
    params.update(new_params)

    return request.base_url + '?' + urlencode(encode_obj(params), doseq=True)
