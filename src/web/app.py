from flask import Flask
from web.models.db import DB
from web.routes import register_all

def create_app():
    DB.get().run()

    app = Flask(__name__, static_folder=None)
    register_all(app)
    
    return app