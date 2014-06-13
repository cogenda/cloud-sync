# -*- coding:utf-8 -*-
import os

# Dummy settings for `django-storages`.

SECRET_KEY='cogenda-cloud-sync'
MEDIA_URL=''
MEDIA_ROOT=''
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_STORAGE_BUCKET_NAME = 'cogenda'
AWS_QUERYSTRING_AUTH = False
AWS_HEADERS = {
        'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT', 
        'Cache-Control': 'max-age=86400',
        'Vary':'Accept-Encoding',
}
