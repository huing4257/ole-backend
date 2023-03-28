#!/bin/sh
python3 manage.py makemigrations user task
python3 manage.py migrate


uwsgi --module=OleBackend.wsgi:application \
     --env DJANGO_SETTINGS_MODULE=OleBackend.settings \
     --master \
     --http=0.0.0.0:80 \
     --processes=5 \
     --harakiri=20 \
     --max-requests=5000 \
     --vacuum
