"""
Module: api.py

Adds API endpoints for the core service.

Blueprint lists routes for the core API. This is registered in main.py

Routes:
    - /api/health:
        Test endpoint for health checks. Used by Docker

Dependencies:
    - Flask: For creating the web API.
    - logging: For logging errors and warnings.
    - os: For file operations.
"""


# Standard library imports
import logging
import os
from flask import (
    Blueprint,
    Response,
    request,
    jsonify,
    current_app,
)


RELOAD_FILE = '/app/reload.txt'


# Create a Flask blueprint for the API
core_api = Blueprint(
    'web_api',
    __name__
)


@core_api.route(
    '/api/health',
    methods=['GET']
)
def health() -> Response:
    '''
    API endpoint to test the web service.
    Called by health checks to verify the service is running.

    Returns:
        str: Empty string indicating the service is healthy.
        200: HTTP status code indicating success.
    '''

    return '', 200


@core_api.route(
    '/api/config',
    methods=['GET', 'PATCH']
)
def api_config() -> Response:
    """
    API endpoint to manage global configuration.

    Methods:
        GET - Called by a module to get the current configuration.
        PATCH - Called by the UI when changes are made.

    PATCH/JSON body should contain the updated configuration.

    Returns:
        JSON response indicating success.
    """

    logging.debug("Global config requested through API")

    # Get the config, refresh the configuration
    app_config = current_app.config['GLOBAL_CONFIG']
    app_config.load_config()

    # GET is used to get the current configuration
    if request.method == 'GET':
        return jsonify(
            {
                'result': 'success',
                'config': app_config.config
            }
        )

    # PATCH is used to update config
    if request.method == 'PATCH':
        # The body of the request
        data = request.json

        result = app_config.update_config(data)

        # If this failed...
        if not result:
            return jsonify(
                {
                    'result': 'error',
                    'message': 'Failed to update configuration'
                }
            )

        # If successful, recycle the workers to apply the changes
        try:
            with open(RELOAD_FILE, 'a'):
                os.utime(RELOAD_FILE, None)
        except Exception as e:
            logging.error("Failed to update reload.txt: %s", e)

        return jsonify(
            {
                'result': 'success'
            }
        )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
