# -*- coding:utf-8 -*-

import sys
import os
import os.path
from scanner.path_scanner import PathScanner
import sqlite3
from sync_public_settings import *


if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'sync_public_settings'

from transporter.transporter_s3 import *
from transporter.transporter_oss import *

if __name__ == "__main__":
    # Set up logger.
    logger = logging.getLogger("Travis")
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

    
    def sync_s3(source, dst):
        # Amazon S3
        try:
            s3 = TransporterS3(callback, error_callback,'Travis')
        except ConnectionError, e:
            print "Error occurred in TransporterS3:", e
            sys.exit(2)
        else:
            s3.start()
            s3.sync_file(source, dst)
            time.sleep(3)
            s3.stop()
    
    def sync_oss(source, dst):
        # AliYun OSS
        try:
            oss = TransporterOSS(callback, error_callback,'Travis')
        except ConnectionError, e:
            print "Error occurred in TransporterOSS:", e
            sys.exit(2)
        else:
            oss.start()
            oss.sync_file(source, dst)
            time.sleep(3)
            oss.stop()

    
    def calculate_transporter_dst(src, relative_paths=[]):
        dst = src
        parent_path=None

        # Strip off any relative paths.
        for relative_path in relative_paths:
            if dst.startswith(relative_path):
                parent_path = SCAN_PATHS[relative_path]
                dst = dst[len(relative_path):]

        # Ensure no absolute path is returned, which would make os.path.join()
        # fail.
        dst = dst.lstrip(os.sep)

        # Prepend any possible parent path.
        if not parent_path is None:
            dst = os.path.join(parent_path, dst)

        return dst

    path = COGENDA_STATIC_HOME
    db = sqlite3.connect("pathscanner.db")
    db.text_factory = unicode # This is the default, but we set it explicitly, just to be sure.
    ignored_dirs = []
    scanner = PathScanner(db, ignored_dirs)
    scanner.initial_scan(COGENDA_STATIC_HOME)
    scanner.scan_tree(COGENDA_STATIC_HOME)
    dbcur = db.cursor()
    dbcur.execute("SELECT * FROM pathscanner WHERE mtime!=-1")
    files_in_dir = dbcur.fetchall()
    for (path, filename, mtime) in files_in_dir:
        source = '%s/%s' %(path, filename)
        dst = calculate_transporter_dst(source, SCAN_PATHS.keys())
        sync_s3(source, dst)
        sync_oss(source, dst)

    print 'Travis CI Sync with OSS & S3 Successfully.'
