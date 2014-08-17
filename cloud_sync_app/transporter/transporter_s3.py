# -*- coding:utf-8 -*-

""" AWS S3 transporter """

from .transporter import *
from storages.backends.s3boto import S3BotoStorage

TRANSPORTER_CLASS = "TransporterS3"

class TransporterS3(Transporter):

    name = 'S3'

    def __init__(self, conf, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        default_acl = 'public-read'
        default_bucket = conf['AWS_STORAGE_BUCKET_NAME']
        default_querystring_auth=False
        if not conf['IS_PUBLIC']:
            default_acl = 'private'
            default_bucket = conf['AWS_STORAGE_BUCKET_PVT_NAME']
            default_querystring_auth=True

        try:
            self.storage = S3BotoStorage(
                    acl= default_acl,
                    bucket= default_bucket.encode('utf-8'),
                    querystring_auth= default_querystring_auth
                    )
        except Exception, e:
            raise ConnectionError(e)
