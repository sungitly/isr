# -*- coding: utf-8 -*-
from wtforms import widgets
from wtforms import IntegerField


class HiddenIntField(IntegerField):
    widget = widgets.HiddenInput()
