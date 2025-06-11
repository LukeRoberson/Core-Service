"""
Module: main.py

Main module for starting the core service and setting up the routes.
This service is responsible for:
    - Loading global configuration
    - Loading plugins and their configuration

Usage:
    This is a Flask application that should run behind a WSGI server inside
        a Docker container.
    Build the Docker image and run it with the provided Dockerfile.

Functions:
    - create_app:
        Creates the Flask application instance and sets up the configuration.

Dependencies:
    - Flask: For creating the web application.
    - Flask-Session: For session management.
    - os: For environment variable access.

Custom Dependencies:
    - api.core_api: For API endpoints of the core service.
"""

from flask import Flask
from flask_session import Session
import os

from api import core_api


def create_app() -> Flask:
    """
    Create the Flask application instance.
    Registers the necessary blueprints for the core service.

    Args:
        None

    Returns:
        Flask: The Flask application instance with the necessary
            configuration and blueprints registered.
    """

    # Create the Flask application
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('api_master_pw')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/app/flask_session'
    Session(app)

    # Register blueprints
    app.register_blueprint(core_api)

    return app


# Setup the Core service
app = create_app()
