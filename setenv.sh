#!/bin/bash
# - Aim to build up cloud sync virtual evironmnet.
# - Author: tim.tang

if [ ! -e venv ]; then
    virtualenv --no-site-packages venv
fi

source venv/bin/activate
export STATIC_DEPS=true
pip install -r requirements.txt
