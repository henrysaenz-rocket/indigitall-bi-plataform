"""Gunicorn WSGI entry point."""

from app.main import dash_app

server = dash_app.server
