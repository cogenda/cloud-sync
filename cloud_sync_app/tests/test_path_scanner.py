# -*- coding:utf-8 -*-

from ..scanner.path_scanner import PathScanner
import sqlite3
from sets import Set

if __name__ == "__main__":
    # Sample usage
    path = unicode("/Users/tim-tang/Work/cogenda-web/assets_rel/static/",'utf-8')
    db = sqlite3.connect("pathscanner.db")
    db.text_factory = unicode # This is the default, but we set it explicitly, just to be sure.
    ignored_dirs = ["CVS", ".svn"]
    scanner = PathScanner(db, ignored_dirs)
    # Force a rescan
    #scanner.purge_path(path)
    scanner.initial_scan(path)

    # Detect changes in a single directory
    # print scanner.scan(path)

    # Detect changes in the entire tree
    report = {}
    report["created"] = Set()
    report["deleted"] = Set()
    report["modified"] = Set()
    for path, result in scanner.scan_tree(path):
        report["created"] = report["created"].union(result["created"])
        report["deleted"] = report["deleted"].union(result["deleted"])
        report["modified"] = report["modified"].union(result["modified"])
    print report
