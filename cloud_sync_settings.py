# -*- coding:utf-8 -*-
import os
import logging

# Dummy settings for `django-storages`.
SECRET_KEY='cogenda-cloud-sync'
MEDIA_URL=''
MEDIA_ROOT=''


########################################################
#               AWS S3 CONFIGURATION                   #           
########################################################
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_STORAGE_BUCKET_NAME = 'cogenda'
AWS_QUERYSTRING_AUTH = False
#The minimum part size(byte) (if there is more than one part).
#This value must be >= 5M
AWS_S3_FILE_BUFFER_SIZE=5*1024*1024
AWS_HEADERS = {
        'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT', 
        'Cache-Control': 'max-age=86400',
        'Vary':'Accept-Encoding',
        }
AWS_DEFAULT_ACL='public-read'


########################################################
#               AliYun OSS CONFIGURATION               #           
########################################################
OSS_ACCESS_URL='oss.aliyuncs.com'
OSS_ACCESS_KEY_ID=os.environ.get('OSS_ACCESS_KEY_ID', None)
OSS_SECRET_ACCESS_KEY=os.environ.get('OSS_SECRET_ACCESS_KEY', None)
OSS_STORAGE_BUCKET_NAME = 'cogenda'
OSS_HEADERS = {
        'Cache-Control': 'max-age=31536000', 
        }
OSS_DEFAULT_ACL = 'public-read'
#The minimum part size(byte) (if there is more than one part).
#This value must be >= 5M
OSS_FILE_BUFFER_SIZE=5*1024*1024


########################################################
#               CLOUD SYNC CONFIGURATION               #           
########################################################
RESTART_AFTER_UNHANDLED_EXCEPTION = False
RESTART_INTERVAL = 10
LOG_FILE = './cloud_sync.log'
PID_FILE = '/tmp/cloud_sync.pid'
PERSISTENT_DATA_DB = './cloud_sync.db'
SYNCED_FILES_DB = './cloud_sync.db'
FSMONITOR_DB = './cloud_sync.db'
CONSOLE_LOGGER_LEVEL = logging.INFO
FILE_LOGGER_LEVEL = logging.INFO
MAX_SIMULTANEOUS_TRANSPORTERS = 10
MAX_TRANSPORTER_QUEUE_SIZE = 1
MAX_TRANSPORTER_POOL_SIZE = 5
QUEUE_PROCESS_BATCH_SIZE = 20
CALLBACKS_CONSOLE_OUTPUT = True
RETRY_INTERVAL=30


########################################################
#                 USER SETTINGS                        #           
########################################################
COGENDA_STATIC_HOME=os.environ.get('COGENDA_STATIC_HOME', None)
COGENDA_MEDIA_HOME=os.environ.get('COGENDA_MEDIA_HOME', None)
SCAN_PATHS={
        unicode(COGENDA_STATIC_HOME,'utf-8'): 'static',
        }
IGNORE_PATHS=[]
TRANSPORTERS=['s3', 'oss']
