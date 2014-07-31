# -*- coding:utf-8 -*-

""" Verify Synced Files """

import httplib
import urlparse
import sqlite3
import sys
from .sync_pub_settings import *
import Queue
import threading
import time
from thread import allocate_lock


dbcon = sqlite3.connect(SYNCED_FILES_DB)
dbcon.text_factory = unicode # This is the default, but we set it explicitly, just to be sure.
dbcur = dbcon.cursor()
num_files = dbcur.execute("SELECT COUNT(*) FROM synced_files").fetchone()[0]
dbcur.execute("SELECT input_file, url, server FROM synced_files ORDER BY server")

num_files_checked = 0
num_files_invalid = 0
url_queue = Queue.Queue()
progress_queue = Queue.Queue()

lock = allocate_lock()
def worker(url_queue):
    is_active = True
    while is_active:
        url = url_queue.get()
        do_crawl(url)
        if url_queue.empty():
            is_active = False
            break

def do_crawl(url):
    global num_files_checked, num_files_invalid 
    parsed = urlparse.urlparse(url)
    conn = httplib.HTTPConnection(parsed.netloc)
    conn.request("HEAD", parsed.path)
    response = conn.getresponse()
    if not (response.status == 200 and response.reason == 'OK'):
        print "Missing: %s, which should be available at %s (server: %s)" % (input_file, url, server)
        lock.acquire()
        num_files_invalid += 1
        lock.release()
    lock.acquire()
    num_files_checked += 1
    lock.release()
    progress_queue.put((num_files_checked, num_files_invalid))
    
def display_progress(progress_queue):
    # make crawler progress
    while True:
        (num_files_checked, num_files_invalid) = progress_queue.get() 
        percentage = num_files_checked * 100.0 / num_files
        progress = '|'*int(round(percentage))
        spaces = ' '*(100 - len(progress))
        sys.stdout.write("\r%3d%% [%s] (%d/%d)" % (percentage, (progress + spaces), num_files_checked, num_files))
        sys.stdout.flush()
        if num_files_checked == num_files:
            break

def print_results():
    print "\n"
    print "//" + "-"*28
    caption = "SYNCED FILES RECORDS"
    syced_files = "SYNCED FILES NUM => [%d]" % (num_files_checked)
    failed_files = "FAILED FILES NUM => [%d]" % (num_files_invalid)
    print "// "+ caption + " "*20 
    print "//" + "-"*28 
    print "// "+ syced_files 
    print "//" + "-"*28
    print "// "+ failed_files 
    print "//" + "-"*28



if __name__ == '__main__':
    WORKER_NUM = 10
    threads = []
    for input_file, url, server in dbcur.fetchall():
        url_queue.put(url)

    for idx in range(WORKER_NUM):
        crawler = threading.Thread(target=worker, args = (url_queue,)) 
        crawler.start()
        threads.append(crawler)

    progress_bar = threading.Thread(target=display_progress, args =(progress_queue,))
    progress_bar.setDaemon(True)
    progress_bar.start() 
    threads.append(progress_bar)

    for thread in threads:
        thread.join()

    print_results()

