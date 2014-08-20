# -*- coding:utf-8 -*-

import time
import Queue
from ..persistent.persistent_list import *

class RetryHandler(object):

    def __init__(self, settings, logger, lock):
        self.lock = lock
        self.settings = settings
        self.logger = logger
        self.last_retry = 0

    def setup_retry(self):
        self.failed_files = PersistentList("failed_files_list", self.settings['PERSISTENT_DATA_DB'])
        self.num_failed_files = len(self.failed_files)
        self.logger.warning("Setup: initialized 'failed_files' persistent list, contains %d items." % (self.num_failed_files))
        self.retry_queue = Queue.Queue()
        # self.next_retry_files_num = 0
        return self.retry_queue, self.num_failed_files

    def process_retry_queue(self):
        processed = 0

        while processed < self.settings['QUEUE_PROCESS_BATCH_SIZE'] and self.retry_queue.qsize() > 0:
            # Retry queue -> failed files list.
            self.lock.acquire()
            (input_file, event, server) = self.retry_queue.get()

            if (input_file, event) not in self.failed_files:
                self.failed_files.append((input_file, event, server))
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

    def allow_retry(self, transport_queue):
        num_failed_files = len(self.failed_files)
        should_retry = self.last_retry + self.settings['RETRY_INTERVAL'] < time.time()

        if num_failed_files > 0 and should_retry:
            failed_items = []

            processed = 0
            while processed < self.settings['QUEUE_PROCESS_BATCH_SIZE'] and processed < len(self.failed_files):
                item = self.failed_files[processed]
                failed_items.append(item)
                for server in self.settings['TRANSPORTERS']:
                    if server == item[2]:
                        transport_queue[server].put((item[0], item[1], server, item[0]))
                processed += 1

            for item in failed_items:
                self.failed_files.remove(item)

            self.last_retry = time.time()
            self.logger.warning("Moved %d items from the 'failed_files' persistent list into the 'pipeline' persistent queue." % (processed))
