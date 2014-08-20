# -*- coding:utf-8 -*-

""" Verify Synced Files """

import httplib
import urlparse
import sqlite3
import sys
import Queue
import threading

dbcon = sqlite3.connect('./cloud_sync.db')
dbcon.text_factory = unicode
dbcur = dbcon.cursor()
num_files = dbcur.execute("SELECT COUNT(*) FROM synced_files").fetchone()[0]
dbcur.execute("SELECT input_file, url, server FROM synced_files ORDER BY server")

num_files_checked = 0
files_invalid = []
files_unverified = []
url_queue = Queue.Queue()
progress_queue = Queue.Queue()

lock = threading.Lock()
def worker(url_queue):
    is_active = True
    while is_active:
        (url, input_file, server) = url_queue.get()
        do_crawl(url, input_file, server)
        if url_queue.empty():
            is_active = False
            break

def do_crawl(url, input_file, server):
    global num_files_checked
    try:
        parsed = urlparse.urlparse(url)
        conn = httplib.HTTPConnection(parsed.netloc, timeout=5)
        conn.request("HEAD", parsed.path)
        response = conn.getresponse()
        if not response or not (response.status == 200 and response.reason == 'OK'):
            # print "Missing: %s, which should be available at %s (server: %s)" % (input_file, url, server)
            files_invalid.append((input_file, server))
    except Exception:
        files_unverified.append((input_file, server))
    finally:
        lock.acquire()
        num_files_checked += 1
        progress_queue.put(num_files_checked)
        lock.release()

def display_progress(progress_queue):
    # make crawler progress
    while True:
        num_files_checked = progress_queue.get()
        percentage = num_files_checked * 100.0 / num_files
        progress = '|'*int(round(percentage))
        spaces = ' '*(100 - len(progress))
        sys.stdout.write("\r%3d%% [%s] (%d/%d)" % (percentage, (progress + spaces), num_files_checked, num_files))
        sys.stdout.flush()
        if num_files_checked == num_files:
            print ' - Verification Completed!'
            break

def print_results():
    print "\n"
    print "#" + "-"*28
    caption = "SYNCED FILES RECORDS"
    caption_syced_files = "SYNCED FILES NUM => [%d]" % (num_files_checked)
    caption_failed_files = "FAILED FILES NUM => [%d]" % (len(files_invalid))
    caption_unverified_files = "UN-VERIFIED FILES NUM => [%d]" % (len(files_unverified))
    print "# " + caption + " " * 20
    print "#" + "-" * 28
    print "# " + caption_syced_files
    print "#" + "-" * 28
    print "# " + caption_failed_files
    if len(files_invalid) > 0:
        print "#" + "-" * 28
        for (failed_file, server) in files_invalid:
            print "# [%s] - %s" % (server, failed_file)
    print "#" + "-"*28
    print "# " + caption_unverified_files
    if len(files_unverified) > 0:
        print "#" + "-" * 28
        for (unverified_file, server) in files_unverified:
            print "# [%s] - %s" % (server, unverified_file)
    print "#" + "-" * 28

if __name__ == '__main__':
    WORKER_NUM = 10
    threads = []
    for input_file, url, server in dbcur.fetchall():
        url_queue.put((url, input_file, server))

    try:
        if len(dbcur.fetchall()) > 0:
            for idx in range(WORKER_NUM):
                crawler = threading.Thread(target=worker, args=(url_queue,))
                crawler.start()
                threads.append(crawler)

            progress_bar = threading.Thread(target=display_progress, args=(progress_queue,))
            progress_bar.setDaemon(True)
            progress_bar.start()
            threads.append(progress_bar)
            for thread in threads:
                thread.join()
    except KeyboardInterrupt, SystemExit:
        print '\n! Received keyboard interrupt, quitting verification threads.\n'
        sys.exit()

    print_results()
