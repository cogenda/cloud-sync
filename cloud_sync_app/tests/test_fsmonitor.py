
# -*- coding:utf-8 -*-
from ..fsmonitor.fsmonitor import *

if __name__ == "__main__":
    import time

    def callbackfunc(monitored_path, event_path, event, discovered_through):
        print "CALLBACK FIRED, params: monitored_path=%s', event_path='%s', event='%d', discovered_through='%s'" % (monitored_path, event_path, event, discovered_through)

    fsmonitor_class = get_fsmonitor()
    print "Using class", fsmonitor_class
    fsmonitor = fsmonitor_class(callbackfunc, True)
    fsmonitor.start()
    fsmonitor.add_dir(unicode('/Users/tim-tang/Work/test','utf-8'), FSMonitor.CREATED | FSMonitor.MODIFIED | FSMonitor.DELETED)
    time.sleep(30)
    fsmonitor.stop()
