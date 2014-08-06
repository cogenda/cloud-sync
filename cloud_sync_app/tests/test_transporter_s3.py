# -*- coding:utf-8 -*-

import sys
import os
import os.path

if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cloud_sync_app.django_storage_module'

from ..transporter.transporter_s3 import *

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


    # Amazon S3
    try:
        s3 = TransporterS3(callback, error_callback,'Test')
    except ConnectionError, e:
        print "Error occurred in TransporterS3:", e
    else:
        s3.start()
        s3.sync_file('/Users/tim-tang/Desktop/arctic-wolf.jpg')
        s3.sync_file('/Users/tim-tang/Desktop/logo.jpg')
        s3.sync_file("/Users/tim-tang/Desktop/arctic-wolf.jpg", "/Users/tim-tang/Desktop/arctic-wolf.jpg", Transporter.DELETE)
        time.sleep(5)
        s3.stop() 
