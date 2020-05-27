#!/usr/bin/env sh

if [ ! -f "$HOME/gunicorn_drp_server.pid" ]; then
    echo "Starting server..."
    gunicorn wsgi:app \
        --bind 0.0.0.0:8000 \
        --pid $HOME/gunicorn_drp_server.pid \
        --daemon
else
    echo "Restarting server..."
    kill -HUP `cat $HOME/gunicorn_drp_server.pid`
fi
