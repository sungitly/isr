# -*- coding: utf-8 -*-
from application import create_app
from celery import Celery


def make_celery(app):
    cly = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    cly.conf.update(app.config)
    TaskBase = cly.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                result = TaskBase.__call__(self, *args, **kwargs)
                return result

    cly.Task = ContextTask
    return cly


app = create_app()

celery = make_celery(app)


def async_call(task_name, args=None, kwargs=None, countdown=None,
               eta=None, task_id=None, producer=None, connection=None,
               router=None, result_cls=None, expires=None,
               publisher=None, link=None, link_error=None,
               add_to_parent=True, reply_to=None, **options):
    celery.send_task(task_name, args, kwargs, countdown, eta, task_id, producer, connection, router, result_cls,
                     expires, publisher, link, link_error,
                     add_to_parent, reply_to, **options)
