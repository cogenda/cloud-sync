# Makefile for cogenda cloud sync 

.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo ""
	@echo "  run-pub       to sync public files with cloud sync service"
	@echo "  run-pvt       to sync private files with cloud sync service"
	@echo "  stop          to shutdown cloud sync service"
	@echo "  verify        to verify synced files is missing"
	@echo ""


.PHONY: run-pub
run-pub: 
	@python -m cloud_sync_app.cloud_sync pub

.PHONY: run-pvt
run-pvt:
	@python -m cloud_sync_app.cloud_sync pvt

stop:
	@cat /tmp/cloud_sync.pid|xargs kill -9

verify:
	@./venv/bin/python -m cloud_sync_app.verify

deploy:
	@fab tarball upload_dist install_venv install_app restart_app clean

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*.DS_Store' -exec rm -f {} +
	@find . -name '~' -exec rm -f {} +
