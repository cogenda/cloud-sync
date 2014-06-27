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

SYNC_PUBLIC_SETTING=sync_public_settings.py
SYNC_PRIVATE_SETTINGS=sync_private_settings.py

.PHONY: run-public
run-public: 
	@python cloud_sync.py ${SYNC_PUBLIC_SETTING}

.PHONY: run-private
run-private:
	@python cloud_sync.py ${SYNC_PRIVATE_SETTING}

travis:
	@python travis_sync.py

verify:
	@python verify.py

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*.DS_Store' -exec rm -f {} +
	@find . -name '~' -exec rm -f {} +
