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
from fabric.context_managers import shell_env

####################################################################
#           Cloud Sync Service Auto Deployment                     #
####################################################################

# Internal variables
APP_PATH = "~/apps"
CLOUD_SYNC_HOME = "%s/cloud-sync" % (APP_PATH)
VENV_HOME = "%s/venv" % (CLOUD_SYNC_HOME)
ENV_ACTIVATE = "source %s/venv/bin/activate" % CLOUD_SYNC_HOME 

TRAVIS_SSH_KEY = "~/.ssh/id_rsa"
env.host_string = "85.159.208.213"
env.user = "tim"
env.key_filename = TRAVIS_SSH_KEY
env.port = 22

@_contextmanager
def virtualenv():
    with cd(CLOUD_SYNC_HOME):
        with prefix(ENV_ACTIVATE):
            yield

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
    if not exists(VENV_HOME):
        run('virtualenv %s/venv' % CLOUD_SYNC_HOME)
    print(red("Virtualenv installation succeed!"))

def install_app():
    """
    Installation cloud sync app package:
    """
    dist = local('python setup.py --fullname', capture=True).strip()
    with cd('~/tmp/%s' % dist):
        run('cp -f ~/tmp/%s/cloud_sync_app/sync_pub_settings.py %s' % (dist, CLOUD_SYNC_HOME))
        run('cp -f ~/tmp/%s/cloud_sync_app/sync_pvt_settings.py %s' % (dist, CLOUD_SYNC_HOME))
        run('cp -f ~/tmp/%s/cloud_sync_app/bootstrap.sh %s' % (dist, CLOUD_SYNC_HOME))
        run('rm -f %s/*.pyc' % CLOUD_SYNC_HOME)
        run('%s/venv/bin/python setup.py install' % CLOUD_SYNC_HOME)
    print(red("Auto install cloud sync service succeed!"))

def restart_app():
    with virtualenv():
        #run("cat /tmp/cloud_sync.pid | xargs kill -9")
        run("ps -ef | grep 'cloud_sync' | grep -v 'grep' | awk '{print $2}' | xargs kill -9")
        run("./bootstrap.sh")
        run("ps -ef | grep 'cloud_sync'")
    print(red("Restart Cloud Sync Service Succeed!"))

def clean():
    """Clean packages on server."""
    dist = local('python setup.py --fullname', capture=True).strip()
    run('rm -rf ~/tmp/%s' % dist)
    print(red("Auto Housekeeping succeed!"))

