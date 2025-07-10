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
    - global_config:
        Loads the global configuration for the core service.
    - create_app:
        Creates the Flask application instance and sets up the configuration.

Dependencies:
    - Flask: For creating the web application.
    - Flask-Session: For session management.
    - os: For environment variable access.
    - logging: For logging messages to the terminal.

Custom Dependencies:
    - api.core_api: For API endpoints of the core service.
    - config.GlobalConfig: For loading global configuration.
    - plugins.PluginConfig: For loading plugin configurations.
    - docker_api.DockerApi: For interacting with the Docker host.
"""


# Standard library imports
from flask import Flask
from flask_session import Session
import os
import logging

# Custom imports
from api import core_api
from config import GlobalConfig
from plugins import PluginConfig


def global_config() -> GlobalConfig:
    """
    Load the global configuration for the web service.
    This function initializes the GlobalConfig class

    Args:
        None

    Returns:
        GlobalConfig: An instance of the GlobalConfig class with loaded
            configuration.
    """
    config = GlobalConfig()
    config.load_config()
    return config


def plugin_config() -> PluginConfig:
    """
    Load the plugin configuration for the entire app.

    Returns:
        PluginConfig: An instance of the PluginConfig class with loaded
            plugin configurations.
    """

    config = PluginConfig()
    config.load_config()

    logging.info("%s plugins loaded", len(config))
    for plugin in config:
        logging.debug(
            "Plugin '%s' loaded with webhook URL: %s",
            plugin['name'],
            plugin['webhook']['safe_url']
        )

    return config


def logging_setup() -> None:
    """
    Set up a root logger for the web service.
    This function configures the logging level based on the global
    configuration.

    Args:
        None

    Returns:
        None
    """

    # Set up the logging level based on the configuration
    log_level_str = app_config.config['web']['logging-level'].upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Configure the logging
    logging.basicConfig(level=log_level)
    print(f"Logging level set to: {log_level_str}")


def create_app(
    plugins: PluginConfig,
    config: GlobalConfig,
) -> Flask:
    """
    Create the Flask application instance.
    Registers the necessary blueprints for the core service.

    Args:
        plugins (PluginConfig): The plugin configuration instance.
        config (GlobalConfig): The global configuration instance.

    Returns:
        Flask: The Flask application instance with the necessary
            configuration and blueprints registered.
    """

    # Create the Flask application
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('api_master_pw')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/app/flask_session'
    app.config['GLOBAL_CONFIG'] = config
    app.config['PLUGIN_LIST'] = plugins
    Session(app)

    # Register blueprints
    app.register_blueprint(core_api)

    return app


# Setup the Core service
app_config = global_config()
logging_setup()
plugin_list = plugin_config()
app = create_app(
    plugins=plugin_list,
    config=app_config
)
