# -*- coding: utf-8 -*-
from urlparse import urlparse, urljoin

from flask import request, url_for


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def url_for_pagination(page):
    """Generate url for pagination."""
    view_args = request.view_args.copy()
    args = request.args.copy().to_dict()
    combined_args = dict(view_args.items() + args.items())
    combined_args['page'] = page
    return url_for(request.endpoint, **combined_args)


def back_url(default_back_url=None):
    result = default_back_url

    for url in request.values.get('back_url'), request.referrer:
        if not url:
            continue
        if is_safe_url(url):
            return url

    return result


def url_for_back(back_endpoint=None):
    if back_endpoint:
        return url_for(back_endpoint)
    elif request.referrer and is_safe_url(request.referrer):
        return request.referrer
    else:
        return url_for("site.index")
