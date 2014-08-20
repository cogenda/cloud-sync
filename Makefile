# Makefile for cogenda cloud sync 

.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo ""
	@echo "  run           to sync files with cloud sync service"
	@echo "  stop          to shutdown cloud sync service"
	@echo "  verify        to statistic synced files [synced|invalide|unverified]"
	@echo "  deploy        to deploy cloud sync service into Linode production environment"
	@echo ""


.PHONY: run
run: 
	@python -m cloud_sync_app.cloud_sync ./cloud_sync.yml

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

pylint:
	@flake8 cloud_sync_app
