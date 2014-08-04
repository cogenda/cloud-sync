# -*- coding:utf-8 -*-

import os
import sys
import time
from ..persistent.persistent_list import *

""" TODO: configuration """

class RetryHandler(object):

    def __init__(self, settings, logger, lock):
        self.lock = lock
        self.settings = settings
        self.logger = logger
        self.last_retry = 0

    def setup_retry(self, transport_queue):
        self.failed_files = PersistentList("failed_files_list", PERSISTENT_DATA_DB)
        # TODO: failed files to combine
        num_failed_files = len(self.failed_files)
        self.logger.warning("Setup: initialized 'failed_files' persistent list, contains %d items." % (num_failed_files))
        self.retry_queue = Queue.Queue()
        self.transport_queue = transport_queue

    def process_retry_queue(self):
        processed = 0

        while processed < QUEUE_PROCESS_BATCH_SIZE and self.retry_queue.qsize() > 0:
            # Retry queue -> failed files list.
            # And remove from files in pipeline.
            self.lock.acquire()
            (input_file, event) = self.retry_queue.get()

            if (input_file, event) not in self.failed_files:
                self.failed_files.append((input_file, event))
                already_in_failed_files = False
            else:
                already_in_failed_files = True
            self.lock.release()

            # Log.
            if not already_in_failed_files:
                self.logger.warning("Retry queue -> 'failed_files' persistent list: '%s'. Retrying later." % (input_file))
            else:
                self.logger.warning("Retry queue -> 'failed_files' persistent list: '%s'. File already being retried later." % (input_file))
            processed += 1

    def allow_retry(self):
        num_failed_files = len(self.failed_files)
        should_retry = self.last_retry + RETRY_INTERVAL < time.time()
        
        if num_failed_files > 0 and should_retry:
            failed_items = []

            processed = 0
            while processed < QUEUE_PROCESS_BATCH_SIZE and processed < len(self.failed_files):
                item = self.failed_files[processed]
                failed_items.append(item)
                for server in TRANSPORTERS:
                    self.transport_queue[server].put((item[0], item[1], server, item[0]))
                processed += 1
            
            for item in failed_items:
                self.failed_files.remove(item)

            self.last_retry = time.time()
            self.logger.warning("Moved %d items from the 'failed_files' persistent list into the 'pipeline' persistent queue." % (processed))
