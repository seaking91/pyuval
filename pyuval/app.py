#!/usr/bin/python3

import os
from flask import Flask
from .routes import bp
import yaml

def createOtpServer(config=None):
    app = Flask(__name__)

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        else:
            try:
                env = os.environ.get('FLASK_ENV', 'PRODUCTION')
                with open(os.path.join(app.root_path, config), 'r') as f:
                    c = yaml.load(f, Loader=yaml.FullLoader)
                app.config.update(c.get(env))
            except:
                print("Could not read config file!")

    app.register_blueprint(bp, url_prefix='')
    return app
