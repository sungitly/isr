# -*- coding: utf-8 -*-

import appointment
import customer
import order
import reception
import user
import statustracker
import lookup
import appmeta
import campaign
import calllog
import setting
import store
import middle
import frtinv
import vinrecord
import hwcustomer
import hwaccount
import hwlookup

SYSTEM_USER = user.SuperUser(id=-1000, username='system')
ANONYMOUS_USER = user.Visitor(id=-1001, username='anonymous')
