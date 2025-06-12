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

Custom Dependencies:
    - docker_api.DockerApi: For interacting with the Docker host.
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

# Custom imports
from docker_api import DockerApi


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
def health() -> tuple[str, int]:
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

    # If the method is not GET or PATCH, return a 405 Method Not Allowed
    response = jsonify({'result': 'error', 'message': 'Method not allowed'})
    response.status_code = 405
    return response


@core_api.route(
    '/api/containers',
    methods=['GET']
)
def api_containers() -> Response:
    """
    API endpoint to get the status of service containers.

    Returns:
        JSON response with the status of all running containers.
    """

    # Service containers, as they are defined in the compose file.
    service_containers = [
        "core",
        "web-interface",
        "security",
        "logging",
        "teams",
        "scheduler",
    ]

    container_list = []
    for service in service_containers:
        with DockerApi() as dockerman:
            container_details = dockerman.container_status(service)
            if container_details:
                container_list.append(container_details)
            else:
                logging.warning(
                    "Container %s not found or not running", service
                )
                details = {
                    'name': service,
                    'title': 'missing',
                    'description': 'unknown',
                    'service_name': service,
                    'version': 'unknown',
                    'status': 'container not found',
                    'health': 'unknown',
                }
                container_list.append(details)

    return jsonify(
        {
            'result': 'success',
            'services': container_list
        }
    )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
