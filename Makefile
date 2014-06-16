# Makefile for cogenda cloud sync 
#

.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo ""
	@echo "  run              to run cloud sync service"
	@echo "  run-hard         to clean db files and restart sync service"
	@echo "  verify           to verify synced files valid or not"
	@echo ""

run: 
	@python cloud_sync.py

.PHONY: run-hard
run-hard: 
	@rm -rf *.log
	@rm -rf *.db
	@python cloud_sync.py

verify:
	@python verify.py

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*.DS_Store' -exec rm -f {} +
	@find . -name '~' -exec rm -f {} +
