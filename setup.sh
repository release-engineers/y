#!/usr/bin/env bash

python -m venv venv
source venv/bin/activate || source venv/Scripts/activate
pip install -r requirements.txt
