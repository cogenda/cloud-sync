#!/bin/bash
# - Aim to startup cloud sync service.
# - author: tim.tang

source ~/.bashrc
python -m cloud_sync_app.cloud_sync pub &
