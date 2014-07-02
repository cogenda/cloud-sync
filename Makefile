# Makefile for cogenda cloud sync 
#

.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo ""
	@echo "  run-public       to run cloud sync service"
	@echo "  run-private      to clean db files and restart sync service"
	@echo "  verify           to verify synced files valid or not"
	@echo ""


.PHONY: run-pub
run-pub: 
	@python cloud_sync.py pub

.PHONY: run-pvt
run-pvt:
	@python cloud_sync.py pvt

travis:
	@python travis_sync.py

verify:
	@python verify.py

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*.DS_Store' -exec rm -f {} +
	@find . -name '~' -exec rm -f {} +
