# -*- coding:utf-8 -*-

"""
Cloud Sync application auto deployment tool.
- Make tarball and uplood to production environmnet.
- Install app in production.
- Restart cloud-sync app service.
"""

from fabric.api import *
from fabric.contrib.files import exists
from fabric.colors import green, red
from contextlib import contextmanager as _contextmanager

####################################################################
#           Cloud Sync Service Auto Deployment                     #
####################################################################

# Internal variables
APP_PATH = "~/apps"
CLOUD_SYNC_HOME = "%s/cloud-sync" % (APP_PATH)
DEPLOY_USER = "tim"
DEPLOY_HOST = "85.159.208.213"
TRAVIS_SSH_KEY = "~/.ssh/id_rsa"
VENV_HOME = "%s/venv" % (CLOUD_SYNC_HOME)

@_contextmanager
def virtualenv():
    with cd(CLOUD_SYNC_HOME):
        with prefix(ENV_ACTIVATE):
            yield

def prepare():
    """Prepare to login to production server."""
    env.host_string = DEPLOY_HOST
    env.user = DEPLOY_USER
    env.key_filename = TRAVIS_SSH_KEY
    env.port = 22
    print(red("Login Cloud Sync Production Server Succeed!"))


def tarball():
    """Create tarball for Cloud Sync service."""
    local('python setup.py sdist --formats=gztar', capture=False)


def upload_dist():
    """Upload tarball to the production server."""
    dist = local('python setup.py --fullname', capture=True).strip()
    if not exists('~/tmp'):
        run('mkdir -p ~/tmp')
    put('dist/%s.tar.gz' % dist, '~/tmp/cloud-sync.tar.gz')
    with cd('~/tmp'):
        run('tar xzf ~/tmp/cloud-sync.tar.gz')

def install_venv():
    if not exists(CLOUD_SYNC_HOME):
        run('mkdir -p %s' % CLOUD_SYNC_HOME)
    if not exists(CLOUD_SYNC_HOME):
        run('virtualenv %s/venv' % CLOUD_SYNC_HOME)
    print(red("Virtualenv installation succeed!"))

def install_app():
    """
    Installation cloud sync app package:
    """
    dist = local('python setup.py --fullname', capture=True).strip()
    with cd('~/tmp/%s' % dist):
        run('%s/venv/bin/python setup.py install' % CLOUD_SYNC_HOME)
    print(red("Auto install cloud sync service succeed!"))

def restart_app():
    with virtualenv():
        run("cat /tmp/cloud_sync.pid | xargs kill -9")
        run("python -m cloud_sync_app.cloud_sync pub &")
    print(red("Restart Cloud Sync Service Succeed!"))

def clean():
    """Clean packages on server."""
    dist = local('python setup.py --fullname', capture=True).strip()
    run('rm -rf ~/tmp/%s' % dist)
    print(red("Auto Housekeeping succeed!"))

