"""
Module: api.py

Adds API endpoints for the core service.

Blueprint lists routes for the core API. This is registered in main.py

Functions:
    - get_plugin_by_name: Helper function to find a plugin by its name.
    - recycle_workers: Recycles workers by touching a reload file.
    - error_response: Standardized error response for the API.
    - success_response: Standardized success response for the API.

Routes:
    - /api/health:
        Test endpoint for health checks. Used by Docker
    - /api/config:
        GET: Retrieve the current global configuration.
        PATCH: Update the global configuration.
    - /api/plugins:
        GET: Retrieve configuration for a specific plugin or all plugins.
        POST: Add a new plugin.
        PATCH: Update an existing plugin.
        DELETE: Remove a plugin.
    - /api/containers:
        GET: Retrieve the status of service containers.

Dependencies:
    - Flask: For creating the web API.
    - logging: For logging errors and warnings.
    - os: For file operations.

Custom Dependencies:
    - docker_api.DockerApi: For interacting with the Docker host.
    - config.GlobalConfig: For managing global configuration.
    - plugins.PluginConfig: For managing plugin configurations.
"""


# Standard library imports
import logging
import os
from typing import Optional
from flask import (
    Blueprint,
    Response,
    request,
    current_app,
    jsonify,
    make_response
)

# Custom imports
from docker_api import DockerApi
from config import GlobalConfig
from plugins import PluginConfig


RELOAD_FILE = '/app/reload.txt'


# Create a Flask blueprint for the API
core_api = Blueprint(
    'web_api',
    __name__
)


def get_plugin_by_name(
    plugin_list: 'PluginConfig',
    plugin_name: str
) -> Optional[dict]:
    """
    Find a plugin's configuration by its name.

    Args:
        plugin_list (PluginConfig): The plugin configuration object.
        plugin_name (str): The name of the plugin to find.
    """

    for plugin in plugin_list.config:
        if plugin['name'] == plugin_name:
            return plugin

    return None


def recycle_workers() -> None:
    """
    Recycle the workers by touching the reload file.
    This is used to apply configuration changes.

    Args:
        None

    Returns:
        None
    """

    try:
        with open(RELOAD_FILE, 'a'):
            os.utime(RELOAD_FILE, None)

    except Exception as e:
        logging.error("Failed to update reload.txt: %s", e)


def error_response(
    message: str,
    status: int = 400,
) -> Response:
    """
    Standardized error response for the API.

    Args:
        message (str): The error message to return.
        status (int): The HTTP status code for the error. Defaults to 400.

    Returns:
        Response: A Flask response object with the error message
            and status code.
    """

    return make_response(
        jsonify(
            {
                'result': 'error',
                'message': message
            }
        ),
        status
    )


def success_response(
    message: Optional[str] = None,
    data: Optional[dict] = None,
    status: int = 200,
) -> Response:
    """
    Standardized success response for the API.

    Args:
        message (str, optional): A success message to include in the response.
        data (dict, optional): Additional data to include in the response.
        status (int): The HTTP status code for the response. Defaults to 200.

    Returns:
        Response: A Flask response object with the success message and data.
    """

    # Standard response structure
    resp = {'result': 'success'}

    # Add optional message and data if provided
    if message:
        resp['message'] = message
    if data:
        resp.update(data)

    # Create and return the response
    return make_response(jsonify(resp), status)


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
    app_config: GlobalConfig = current_app.config['GLOBAL_CONFIG']
    app_config.load_config()

    # GET is used to get the current configuration
    if request.method == 'GET':
        return success_response(
            data={
                'config': app_config.config
            }
        )

    # PATCH is used to update config
    if request.method == 'PATCH':
        # The body of the request
        data = request.json
        if data is None:
            return error_response('No data provided')

        result = app_config.update_config(data)

        # If this failed...
        if not result:
            return error_response('Failed to update configuration')

        # If successful, recycle the workers to apply the changes
        try:
            with open(RELOAD_FILE, 'a'):
                os.utime(RELOAD_FILE, None)
        except Exception as e:
            logging.error("Failed to update reload.txt: %s", e)

        return success_response('Configuration updated successfully')

    # If the method is not GET or PATCH, return a 405 Method Not Allowed
    return error_response(
        'Method not allowed',
        status=405
    )


@core_api.route(
    '/api/plugins',
    methods=['GET', 'POST', 'PATCH', 'DELETE']
)
def api_plugins() -> Response:
    """
    API endpoint to manage plugins.
    Called by the Web Interface when changes are made.

    Methods:
        GET - Retrieve config for a specific plugin, or a list of all plugins.
        POST - Add a new plugin.
        PATCH - Update an existing plugin.
        DELETE - Remove a plugin.

    POST/JSON body should contain the plugin configuration.

    PATCH/JSON body should contain the updated plugin configuration.

    DELETE/JSON body should contain the name of the plugin to remove.

    Returns:
        JSON response indicating success.
    """

    # Get the config and refresh
    plugin_config: PluginConfig = current_app.config['PLUGIN_LIST']
    plugin_config.load_config()

    # GET is used to get the current configuration for a specific plugin
    if request.method == 'GET':
        # Get the name of the plugin from the request headers
        plugin_name = request.headers.get('X-Plugin-Name')
        if not plugin_name:
            return make_response(
                jsonify(
                    {
                        'result': 'error',
                        'message': 'Missing X-Plugin-Name header'
                    }
                ),
                400
            )

        # If needed, get a list of all plugins
        if plugin_name == 'all':
            return make_response(
                jsonify(
                    {
                        "result": "success",
                        "plugins": plugin_config.config
                    }
                ),
                200
            )

        # Find the plugin by name
        plugin = get_plugin_by_name(
            plugin_list=plugin_config,
            plugin_name=plugin_name,
        )
        if plugin:
            return jsonify(
                {
                    'result': 'success',
                    'plugin': plugin
                }
            )

        else:
            return make_response(
                jsonify(
                    {
                        'result': 'error',
                        'message': f'Plugin {plugin_name} not found'
                    }
                ),
                404
            )

    # POST is used to add a new plugin
    elif request.method == 'POST':
        if not request.json:
            return error_response('No data provided')

        result = plugin_config.register(request.json)
        if not result:
            return error_response('Failed to add plugin')

        recycle_workers()
        return success_response('Plugin added successfully')

    # PATCH to update an existing plugin
    elif request.method == 'PATCH':
        if not request.json:
            return error_response('No data provided')

        result = plugin_config.update_config(request.json)
        if not result:
            return error_response('Failed to update plugin configuration')

        recycle_workers()
        return success_response('Plugin updated successfully')

    # DELETE to remove a plugin
    elif request.method == 'DELETE':
        data = request.json
        if not data or 'name' not in data:
            return error_response('Missing plugin name in request body')

        plugin_name = data['name']
        result = plugin_config.delete(plugin_name)
        if not result:
            return error_response('Plugin not found or could not be deleted')

        recycle_workers()
        return success_response('Plugin deleted successfully')

    # For unknown methods, return a 405 Method Not Allowed
    return error_response(
        'Method not allowed',
        status=405
    )


@core_api.route(
    '/api/containers',
    methods=['GET']
)
def api_containers() -> Response:
    """
    API endpoint to get the status of service containers.

    Accepts an optional 'container' parameter in the query string
        to specify a single container to check.
    If no container is provided, it defaults to a list of service containers
        defined in the compose file.

    Returns:
        JSON response with the status of all running containers.
    """

    # Get the 'container' parameter from the request (query string)
    container = request.args.get('container', None)

    # If a specific container is requested, use that.
    if container:
        containers = [container]

    # Otherwise, use the default list of service containers.
    else:
        # Service containers, as they are defined in the compose file.
        containers = [
            "core",
            "web-interface",
            "security",
            "logging",
            "teams",
            "scheduler",
        ]

    container_list = []
    for service in containers:
        try:
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

        except Exception as e:
            logging.error(
                f"Failed to get container {service} status: {e}"
            )

            return error_response(
                f"Failed to get container {service} status: {e}",
                status=500
            )

    return success_response(
        data={
            'services': container_list
        }
    )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
