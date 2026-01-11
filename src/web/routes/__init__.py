from flask import Flask

from .backend import bp_backend
from .frontend import bp_frontend
from .files import bp_files
from .analytics import bp_analytics

def register_all(app: Flask) -> None:
    app.register_blueprint(bp_backend)
    app.register_blueprint(bp_frontend)
    app.register_blueprint(bp_files)
    app.register_blueprint(bp_analytics)

__all__ = ['register_all']