# -*- coding:utf-8 -*-

""" AWS S3 transporter """

from transporter import *
from storages.backends.s3boto import S3BotoStorage

TRANSPORTER_CLASS = "TransporterS3"


class TransporterS3(Transporter):


    name              = 'S3'
    headers = {
        'Expires':       'Tue, 20 Jan 2037 03:00:00 GMT', # UNIX timestamps will stop working somewhere in 2038.
        'Cache-Control': 'max-age=315360000',             # Cache for 10 years.
        'Vary' :         'Accept-Encoding',               # Ensure S3 content can be accessed from behind proxies.
    }


    def __init__(self, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        # Map the settings to the format expected by S3Storage.
        try:
            self.storage = S3BotoStorage(self.__class__.headers)
        except Exception, e:            
            raise ConnectionError(e)

