# -*- coding:utf-8 -*-

""" AWS S3 transporter """

from transporter import *
from storages.backends.s3boto import S3BotoStorage

TRANSPORTER_CLASS = "TransporterS3"

class TransporterS3(Transporter):

    name = 'S3'

    def __init__(self, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        # Map the settings to the format expected by S3Storage.
        try:
            self.storage = S3BotoStorage()
        except Exception, e:            
            raise ConnectionError(e)
