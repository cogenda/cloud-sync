# -*- coding:utf-8 -*-

""" Verify Synced Files """

import httplib
import urlparse
import sqlite3
import sys
from .sync_pub_settings import *

num_files_checked = 0
num_files_invalid = 0

dbcon = sqlite3.connect(SYNCED_FILES_DB)
dbcon.text_factory = unicode # This is the default, but we set it explicitly, just to be sure.
dbcur = dbcon.cursor()
num_files = dbcur.execute("SELECT COUNT(*) FROM synced_files").fetchone()[0]
dbcur.execute("SELECT input_file, url, server FROM synced_files ORDER BY server")

for input_file, url, server in dbcur.fetchall():
    parsed = urlparse.urlparse(url)
    
    conn = httplib.HTTPConnection(parsed.netloc)
    conn.request("HEAD", parsed.path)
    response = conn.getresponse()
    
    if not (response.status == 200 and response.reason == 'OK'):
        print "Missing: %s, which should be available at %s (server: %s)" % (input_file, url, server)
        num_files_invalid += 1

    num_files_checked += 1

    percentage = num_files_checked * 100.0 / num_files
    progress = '|'*int(round(percentage))
    spaces = ' '*(100 - len(progress))
    sys.stdout.write("\r%3d%% [%s] (%d/%d)" % (percentage, (progress + spaces), num_files_checked, num_files))
    sys.stdout.flush()

print ""
print "//" + "-"*28
caption = "Synced Files Records"
syced_files = "SYNCED FILES NUM => [%d]" % (num_files_checked)
failed_files = "FAILED FILES NUM => [%d]" % (num_files_invalid)
print "// "+ caption + " "*20 
print "//" + "-"*28 
print "// "+ syced_files 
print "//" + "-"*28
print "// "+ failed_files 
print "//" + "-"*28
