"""Gunicorn WSGI entry point."""

from app.main import app

server = app.server
