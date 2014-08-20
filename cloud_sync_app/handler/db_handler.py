# -*- coding:utf-8 -*-

import os
import sqlite3
from ..fsmonitor.fsmonitor import *

class DBHandler(object):

    def __init__(self, settings, logger, lock):
        self.settings = settings
        self.logger = logger
        self.lock = lock

    def setup_db(self):
        self.transported_file_count = 0
        self.db_queue = Queue.Queue()
        # Create connection to synced files DB.
        self.dbcon = sqlite3.connect(self.settings['SYNCED_FILES_DB'])
        self.dbcon.text_factory = unicode
        self.dbcur = self.dbcon.cursor()
        self.dbcur.execute("CREATE TABLE IF NOT EXISTS synced_files(input_file text, transported_file_basename text, url text, server text)")
        self.dbcur.execute("CREATE UNIQUE INDEX IF NOT EXISTS file_unique_per_server ON synced_files (input_file, server)")
        self.dbcon.commit()
        self.dbcur.execute("SELECT COUNT(input_file) FROM synced_files")
        num_synced_files = self.dbcur.fetchone()[0]
        self.logger.warning("Setup: connected to the synced files DB. Contains metadata for %d previously synced files." % (num_synced_files))
        return self.db_queue

    def peek_transported_count(self):
        return self.transported_file_count

    def shutdown(self):
        # Log information about the synced files DB.
        self.dbcur.execute("SELECT COUNT(input_file) FROM synced_files")
        num_synced_files = self.dbcur.fetchone()[0]
        self.logger.warning("Synced files DB contains metadata for [%d] synced files." % (num_synced_files))

    def process_db_queue(self):
        processed = 0
        while processed < self.settings['QUEUE_PROCESS_BATCH_SIZE'] and self.db_queue.qsize() > 0:
            # DB queue -> database.
            self.lock.acquire()
            (input_file, event, processed_for_server, output_file, transported_file, url, server) = self.db_queue.get()
            self.lock.release()
            # Commit the result to the database.
            transported_file_basename = os.path.basename(output_file)
            if event == FSMonitor.CREATED:
                try:
                    self.dbcur.execute("INSERT INTO synced_files VALUES(?, ?, ?, ?)", (input_file, transported_file_basename, url, server))
                    self.dbcon.commit()
                except sqlite3.IntegrityError, e:
                    self.logger.critical("Database integrity error: %s. Duplicate key: input_file = '%s', server = '%s'." % (e, input_file, server))

            elif event == FSMonitor.MODIFIED:
                self.dbcur.execute("SELECT COUNT(*) FROM synced_files WHERE input_file=? AND server=?", (input_file, server))
                if self.dbcur.fetchone()[0] > 0:
                    # Look up the transported file's base name. This
                    # might be different from the input file's base
                    # name due to processing.
                    # self.dbcur.execute("SELECT transported_file_basename FROM synced_files WHERE input_file=? AND server=?", (input_file, server))
                    # old_transport_file_basename = self.dbcur.fetchone()[0]
                    # Update the transported_file_basename and url fields for
                    # the input_file that has been transported.
                    self.dbcur.execute("UPDATE synced_files SET transported_file_basename=?, url=? WHERE input_file=? AND server=?", (transported_file_basename, url, input_file, server))
                    self.dbcon.commit()
                else:
                    self.dbcur.execute("INSERT INTO synced_files VALUES(?, ?, ?, ?)", (input_file, transported_file_basename, url, server))
                    self.dbcon.commit()
            elif event == FSMonitor.DELETED:
                self.dbcur.execute("DELETE FROM synced_files WHERE input_file=? AND server=?", (input_file, server))
                self.dbcon.commit()
            else:
                raise Exception("Non-existing event set.")
            self.logger.debug("DB queue -> 'synced files' DB: '%s' (URL: '%s')." % (input_file, url))
            self.transported_file_count += 1

        processed += 1
