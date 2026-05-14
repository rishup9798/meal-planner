#!/bin/bash
pip install -r /home/site/wwwroot/requirements.txt
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app
