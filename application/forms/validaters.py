# coding: utf-8
from wtforms.validators import StopValidation

from application.utils import validate_mobile


class PhonenumberRequired(object):
    field_flags = ('required', )

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if validate_mobile(field.data):
            return
        if self.message is None:
            message = 'Not validate phone number.'
        else:
            message = self.message
        field.errors[:] = []
        raise StopValidation(message)
