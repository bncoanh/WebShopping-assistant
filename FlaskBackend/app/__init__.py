import os, secrets
from flask import Flask
from flask_cors import CORS

def create_app(test_config = None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, supports_credentials=True)
    app.config.from_mapping(
        SECRET_KEY=secrets.token_hex(),
    )
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.route('/')(lambda: '<h1 style="color:blue; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; font-size:50px; font-weight: bold;">Backend sever is now running!</h1>')

    
    from .models import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import data
    app.register_blueprint(data.bp)

    from . import product
    app.register_blueprint(product.bp)

    from . import tracking
    app.register_blueprint(tracking.bp)

    from . import admin
    app.register_blueprint(admin.bp)

    return app