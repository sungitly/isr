# -*- coding: utf-8 -*-
from blinker import Namespace

_events = Namespace()

# event got fired when new sales logged in system
new_sales_joined = _events.signal('new_sales_joined')

# event got fired when new receptionist logged in system
new_receptionist_joined = _events.signal('new_receptionist_joined')

# event got fired when sales logout
sales_logout = _events.signal('sales_logout')

# event got fired when receptionist logout
receptionist_logout = _events.signal('receptionist_logout')

# event got fired whenever the status of sales is changed.
sales_status_changed = _events.signal('sales_status_changed')

# event got fired when new reception is created to a sales
new_reception_created = _events.signal('new_reception_created')

# event got fired when reception is cancelled
reception_cancelled = _events.signal('reception_cancelled')
