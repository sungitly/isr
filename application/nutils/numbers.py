# -*- coding: utf-8 -*-


def is_float(num):
    try:
        float(num)
    except:
        return False

    return True


def parse_float(num):
    try:
        return float(num)
    except:
        pass

    return None


def parse_int(num, default=None):
    try:
        return int(num)
    except:
        pass

    return default
