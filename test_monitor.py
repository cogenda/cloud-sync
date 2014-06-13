
# -*- coding:utf-8 -*-
from fsmonitor.monitor import FSMonitor

if __name__ == "__main__":
    import time

    def callbackfunc(monitored_path, event_path, event):
        print "CALLBACK FIRED, params: monitored_path=%s', event_path='%s', event='%d'" % (monitored_path, event_path, event)

    fsmonitor_class = get_fsmonitor()
    print "Using class", fsmonitor_class
    fsmonitor = fsmonitor_class(callbackfunc, True)
    fsmonitor.start()
    #path = unicode("/home/jiltang/work/test",'utf-8')
    fsmonitor.add_dir("/home/jiltang/work/test", FSMonitor.CREATED | FSMonitor.MODIFIED | FSMonitor.DELETED)
    time.sleep(30)
    fsmonitor.stop()