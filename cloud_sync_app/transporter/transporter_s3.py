# -*- coding:utf-8 -*-

""" AWS S3 transporter """

from .transporter import *
from storages.backends.s3boto import S3BotoStorage
import boto

TRANSPORTER_CLASS = "TransporterS3"

class TransporterS3(Transporter):

    name = 'S3'

    def __init__(self, conf, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        boto.config.add_section('Boto')
        boto.config.set('Boto','http_socket_timeout','5')
        boto.config.set('Boto','num_retries','2')
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
