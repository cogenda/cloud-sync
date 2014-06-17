# -*- coding:utf-8 -*-

import sys
import os
import os.path

if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cloud_sync_settings'

from transporter.transporter_oss import *

if __name__ == "__main__":
    # Set up logger.
    logger = logging.getLogger("Test")
    logger.setLevel(logging.DEBUG)
    h = logging.StreamHandler()
    h.setLevel(logging.DEBUG)
    logger.addHandler(h)


    def callback(src, dst, url, action):
        print """CALLBACK FIRED:
                    src='%s'
                    dst='%s'
                    url='%s'
                    action=%d""" % (src, dst, url, action)


    def error_callback(src, dst, action):
        print """ERROR CALLBACK FIRED:
                    src='%s'
                    dst='%s'
                    action=%d""" % (src, dst, action)


    # AliYun OSS
    try:
        oss = TransporterOSS(callback, error_callback,'Test')
    except ConnectionError, e:
        print "Error occurred in TransporterS3:", e
    else:
        oss.start()
        oss.sync_file('/home/jiltang/apache-ant-1.9.4-bin.zip')
        #oss.sync_file('/home/jiltang/Koala.jpg', '/home/jiltang/Koala.jpg', Transporter.DELETE)
        time.sleep(5)
        oss.stop() 

