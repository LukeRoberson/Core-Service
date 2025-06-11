"""
Module: api.py

Adds API endpoints for the core service.

Blueprint lists routes for the core API. This is registered in main.py

Routes:
    - /api/health:
        Test endpoint for health checks. Used by Docker

Dependencies:
    - Flask: For creating the web API.
"""


from flask import Blueprint, Response


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
