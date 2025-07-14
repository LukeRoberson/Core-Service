"""
Module: conftest.py

This file contains fixtures and setup code for pytest tests.

Fixtures:
    - `mock_global_config`: Mocks the GlobalConfig object for testing.
    - `mock_plugin_config`: Mocks the PluginConfig object for testing.
    - `app_with_mocks`: Creates a Flask app with mocked dependencies.
    - `client`: Provides a test client for the Flask app.

Dependencies:
    - pytest: Testing framework
    - unittest.mock: For mocking objects and functions
    - flask: Web framework for Python
    - flask.testing: Provides testing utilities for Flask applications

Custom Dependencies:
    - api.core_api: The core API module to be tested
"""

# Standard imports
import sys
import os
import pytest
from unittest.mock import Mock, patch
from flask import Flask
from flask.testing import FlaskClient

# Custom imports
from api import core_api

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_global_config() -> Mock:
    """
    Create a mock object to simulate the GlobalConfig class

    Real class location: config.py::GlobalConfig
    Last verified: 2025-07-11

    Expected structure:
        - config['web']['port']: int
        - config['web']['logging-level']: str
        - config['logging']['url']: str

    Expected methods:
        - load_config() -> None
        - update_config(data: dict) -> bool

    Args:
        None

    Returns:
        Mock: Mock object with the following attributes:
            - config (dict): Configuration dictionary
            - load_config (Mock): Method mock returning None
            - update_config (Mock): Method mock returning True

    Note:
        This mock should be kept synchronized with the real GlobalConfig
        class to prevent test/production drift.
    """

    # Create the mock object and add configuration
    mock_config = Mock()
    mock_config.config = {
        'web': {
            'port': 5000,
            'logging-level': 'info'
        },
        'logging': {
            'url': 'http://logging:5100/api/log'
        }
    }

    # Define the methods we want to mock
    mock_config.load_config.return_value = None
    mock_config.update_config.return_value = True

    # Return the mock object
    return mock_config


@pytest.fixture
def mock_plugin_config() -> Mock:
    """
    Create a mock object to simulate the PluginConfig class

    Real class location: config.py::PluginConfig
    Last verified: 2025-07-11

    Expected structure:
        - config: List[dict] of plugin configurations
        - Each plugin configuration should have:
            - 'name': str - Plugin identifier
            - 'description': str - Human-readable description
            - 'webhook': dict with keys:
                - 'url': str - Webhook endpoint URL
                - 'auth-type': str - Authentication method

    Expected methods:
        - load_config() -> None

    Args:
        None

    Returns:
        Mock: A mock object simulating the PluginConfig class with
            a single test plugin configuration.
    """

    # Create the mock object and add plugin configuration (list of dicts)
    mock_config = Mock()
    mock_config.config = [
        {
            'name': 'Test Plugin',
            'description': 'A test plugin',
            'webhook': {
                'url': 'http://test:5000',
                'auth-type': 'none'
            }
        }
    ]

    # Define the methods we want to mock
    mock_config.load_config.return_value = None

    # Return the mock object
    return mock_config


@pytest.fixture
def app_with_mocks(
    mock_global_config: Mock,
    mock_plugin_config: Mock,
) -> Flask:
    """
    Create a Flask application with mocked configuration dependencies.

    This fixture creates a fully configured Flask app suitable for testing
    by replacing real configuration objects with controlled mock objects.
    The patching ensures that any imports within the api module will
    receive the mocked versions.

    Args:
        mock_global_config: Mock object replacing GlobalConfig
        mock_plugin_config: Mock object replacing PluginConfig

    Returns:
        Flask: A configured Flask application instance with:
            - Testing mode enabled
            - Mocked configuration objects
            - Core API blueprint registered

    Note:
        Uses unittest.mock.patch to ensure imports within the api module
        receive the mocked objects instead of real configuration classes.
    """

    # Patch to replace GlobalConfig and PluginConfig with mocks during import
    with patch('api.GlobalConfig', return_value=mock_global_config), \
         patch('api.PluginConfig', return_value=mock_plugin_config):

        # Create Flask app with test configuration
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['GLOBAL_CONFIG'] = mock_global_config
        app.config['PLUGIN_LIST'] = mock_plugin_config

        # Register the core API blueprint with all endpoints
        app.register_blueprint(core_api)

        return app


@pytest.fixture
def client(
    app_with_mocks: Flask
) -> FlaskClient:
    """
    Create a test client for making HTTP requests to the Flask application.

    Args:
        app_with_mocks: Flask application with mocked dependencies

    Returns:
        FlaskClient: Test client for making HTTP requests during testing

    Example:
        >>> def test_health(client):
        ...     response = client.get('/api/health')
        ...     assert response.status_code == 200
    """

    # A test client from the test Flask app
    return app_with_mocks.test_client()
