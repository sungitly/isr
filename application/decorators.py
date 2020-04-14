# -*- coding: utf-8 -*-
from functools import wraps
import json
import time
import datetime

from application.models.job import JobsRecord
from application.pagination import generate_header_link
from application.utils import CustomizedEncoder, DATE_FORMAT
from flask import current_app, request
from flask.ext.sqlalchemy import Pagination


def render_json_response(target_function):
    @wraps(target_function)
    def wrapper(*args, **kwargs):
        rv = target_function(*args, **kwargs)

        status = headers = None

        # handle tuple response
        if isinstance(rv, tuple):
            rv, status, headers = rv + (None,) * (3 - len(rv))

        rv = dict() if rv is None else rv

        status = 200 if status is None else status
        headers = dict() if headers is None else headers

        # handle Pagination response
        if isinstance(rv, Pagination):
            headers['X-Total-Count'] = rv.total
            headers['Link'] = generate_header_link(request, rv)
            headers['X-Page'] = rv.page
            headers['X-Per-Page'] = rv.per_page
            rv = rv.items

        if headers.get('Content-Type', None) is None:
            headers['Content-Type'] = 'application/json'

        if not isinstance(rv, current_app.response_class):
            rv = current_app.response_class(json.dumps(rv, cls=CustomizedEncoder), headers=headers, status=status)

        return rv

    return wrapper


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        current_app.logger.warning('ISR TIMING >>>>>> %r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te - ts))
        return result

    return timed


def log_job_result(jobname='none', daily=True):
    '''
    jobname: will record in JobsRecord table
    default is function name
    '''

    def decorator(target_function):
        # noinspection PyBroadException
        @wraps(target_function)
        def wrapper(*args, **kwargs):
            force = request.args.get('force', None)
            today = datetime.datetime.now().strftime(DATE_FORMAT)

            if jobname == 'none':
                jobsname = target_function.__name__
            else:
                jobsname = jobname

            if daily and not force:
                job_logger = JobsRecord.get_job_result_by_date(jobsname, today)
                if len(job_logger) != 0:
                    result = JobsRecord()
                    result.start_time = datetime.datetime.now()
                    result.jobname = jobsname
                    result.status = 'failed'
                    result.message = 'The job has been processed'
                    result.save_and_flush()
                    return result

            result = JobsRecord()
            result.jobname = jobsname
            result.start_time = datetime.datetime.now()

            try:
                function_return = target_function(*args, **kwargs)
                result.json_result = json.dumps(function_return, cls=CustomizedEncoder)
            except:
                result.status = 'failed'

            result.complete()
            result.save_and_flush()
            return result

        return wrapper

    return decorator
