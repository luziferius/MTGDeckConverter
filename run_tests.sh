#!/bin/bash

# Try to enable a virtual environment in "venv". If this fails, the system wide installation will be used instead.
source venv/bin/activate

python3 setup.py test
