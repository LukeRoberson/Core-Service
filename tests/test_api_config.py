"""
Module: test_api_config.py

Provides unit tests for the API endpoints. Uses fixtures from conftest.py
    to mock dependencies and create a test client.

Follows the Arrange/Act/Assert (AAA) pattern for tests.
    1. Arrange: Set up the test environment and data; See conftest.py.
    2. Act: Call the API endpoint or function being tested.
    3. Assert: Check the response status code and data.

Classes:
    - `TestApiConfig`: Contains tests for the API configuration endpoints.
    - `TestResponseHelpers`: Contains tests for the response helper functions.

Mocks and Fixtures:
    - `mock_global_config`: Mocks the GlobalConfig object for testing.
    - `mock_plugin_config`: Mocks the PluginConfig object for testing.
    - `app_with_mocks`: Creates a Flask app with mocked dependencies.
    - `client`: Provides a test client for the Flask app.

Dependencies:
    - conftest.py: Contains fixtures and setup code for pytest tests
    - unittest.mock: For mocking objects and functions

Custom Dependencies:
    - api.core_api: The core API module to be tested
"""

# Standard library imports
import json
from flask.testing import FlaskClient
from unittest.mock import (
    patch,
    mock_open,
    Mock,
)

# Custom imports
from api import (
    success_response,
    error_response,
)


class TestApiConfig:
    """
    Contains tests for the core API endpoints related to config management.

    Endpoints tested:
        - /api/health (GET):
            Health check, should return 200 OK with empty body.
        - /api/config (GET):
            Returns current configuration.
        - /api/config (PATCH):
            Updates configuration with provided data.
    """

    def test_health_endpoint(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test the health check endpoint

        Should return 200 OK with an empty body

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        response = client.get('/api/health')

        # Assert (200 OK with empty body)
        assert response.status_code == 200
        assert response.data == b''

    def test_config_get_success(
        self,
        client: FlaskClient,
        mock_global_config: Mock,
    ) -> None:
        """
        Test GET /api/config returns configuration successfully

        Expects:
            200 OK
            JSON body with 'result' and 'config' keys
                'result' should be 'success'
                'config' should match the mock_global_config

        Args:
            client (FlaskClient): The test client for making requests
            mock_global_config (Mock): Mocked GlobalConfig object

        Returns:
            None
        """

        # Act
        response = client.get('/api/config')

        # Assert - Response should be 200 OK
        assert response.status_code == 200

        # Assert - Response should be JSON with expected structure
        data = json.loads(response.data)
        assert data['result'] == 'success'
        assert 'config' in data
        assert data['config'] == mock_global_config.config

        # Verify that load_config was called
        mock_global_config.load_config.assert_called_once()

    def test_config_patch_success(
        self,
        client: FlaskClient,
        mock_global_config: Mock,
    ) -> None:
        """
        Test PATCH /api/config updates configuration successfully

        Expects:
            200 OK
            JSON body with 'result' and 'message' keys
                'result' should be 'success'
                'message' should indicate successful update
            reload file should be touched, indicating config reload

        Args:
            client (FlaskClient): The test client for making requests
            mock_global_config (Mock): Mocked GlobalConfig object

        Returns:
            None
        """

        # Arrange
        update_data = {
            'web': {
                'port': 5001,
                'logging-level': 'debug'
            }
        }

        # Mock file operations for the reload file
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('os.utime') as mock_utime:

            # Act
            response = client.patch(
                '/api/config',
                data=json.dumps(update_data),
                content_type='application/json'
            )

            # Assert - Response should be 200 OK
            assert response.status_code == 200

            # Assert - Response should be JSON with expected structure
            data = json.loads(response.data)
            assert data['result'] == 'success'
            assert data['message'] == 'Configuration updated successfully'

            # Verify that update_config was called with the right data
            mock_global_config.update_config.assert_called_once_with(
                update_data
            )

            # Verify that the reload file was touched
            mock_file.assert_called_once_with('/app/reload.txt', 'a')
            mock_utime.assert_called_once()

    def test_config_patch_no_content_type(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test PATCH /api/config fails when no content type is provided

        Expects:
            415 Unsupported Media Type

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        response = client.patch('/api/config')

        # Assert - 415 Unsupported Media Type
        assert response.status_code == 415

    def test_config_patch_empty_json_body(
        self,
        client: FlaskClient,
    ) -> None:
        """
        Test PATCH /api/config with empty JSON body

        Expects:
            400 Bad Request

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        response = client.patch(
            '/api/config',
            data='',
            content_type='application/json'
        )

        # Assert - Returns 400 for empty JSON body
        assert response.status_code == 400

    def test_config_patch_malformed_json(
        self,
        client: FlaskClient,
    ) -> None:
        """
        Test PATCH /api/config fails with malformed JSON

        Expects:
            400 Bad Request

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        response = client.patch(
            '/api/config',
            data='invalid json',
            content_type='application/json'
        )

        # Assert - Returns 400 for malformed JSON
        assert response.status_code == 400

    def test_config_patch_null_data(
        self,
        client: FlaskClient,
    ) -> None:
        """
        Test PATCH /api/config with explicit null JSON data

        Expects:
            400 Bad Request
            JSON response indicating no data provided

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act - Send valid JSON that represents null
        response = client.patch(
            '/api/config',
            data=json.dumps(None),
            content_type='application/json'
        )

        # Assert - Should return 400 Bad Request
        assert response.status_code == 400

        # Assert - Response should indicate no data provided
        data = json.loads(response.data)
        assert data['result'] == 'error'
        assert data['message'] == 'No data provided'

    def test_config_patch_empty_json_object(
        self,
        client: FlaskClient,
        mock_global_config: Mock
    ) -> None:
        """
        Test PATCH /api/config with empty JSON object

        Expects:
            200 OK
            JSON response indicating success

        Args:
            client (FlaskClient): The test client for making requests
            mock_global_config (Mock): Mocked GlobalConfig object

        Returns:
            None
        """

        # Act
        response = client.patch(
            '/api/config',
            data=json.dumps({}),
            content_type='application/json'
        )

        # Assert - Empty object should be valid
        assert response.status_code == 200

        # Assert - Response should indicate success
        data = json.loads(response.data)
        assert data['result'] == 'success'

        # Verify update_config was called with empty dict
        mock_global_config.update_config.assert_called_once_with({})

    def test_config_patch_invalid_json(
        self,
        client: FlaskClient,
    ) -> None:
        """
        Test PATCH /api/config fails with invalid JSON

        Expects:
            400 Bad Request

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        response = client.patch(
            '/api/config',
            data='invalid json',
            content_type='application/json'
        )

        # Assert - Should return 400 Bad Request
        assert response.status_code == 400

    def test_config_patch_update_fails(
        self,
        client: FlaskClient,
        mock_global_config: Mock
    ) -> None:
        """
        Test PATCH /api/config handles update failure

        Expects:
            400 Bad Request
            JSON response indicating failure to update configuration

        Args:
            client (FlaskClient): The test client for making requests
            mock_global_config (Mock): Mocked GlobalConfig object

        Returns:
            None
        """

        # Arrange
        mock_global_config.update_config.return_value = False
        update_data = {'test': 'data'}

        # Act
        response = client.patch(
            '/api/config',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        # Assert - Should return 400 Bad Request
        assert response.status_code == 400

        # Assert - Response should indicate failure to update
        data = json.loads(response.data)
        assert data['result'] == 'error'
        assert data['message'] == 'Failed to update configuration'

    def test_config_unsupported_method(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test that unsupported HTTP methods return 405

        Expects:
            405 Method Not Allowed

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        response = client.post('/api/config')

        # Assert - Flask handles 405 at framework level
        assert response.status_code == 405

        # Check HTML response contains the expected error message
        response_text = response.data.decode('utf-8')
        assert 'Method Not Allowed' in response_text

    def test_config_multiple_unsupported_methods(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test methods that return 405

        Expects:
            405 Method Not Allowed for POST, PUT, DELETE

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Methods to test that should return 405
        unsupported_methods = [
            client.post,
            client.put,
            client.delete,
        ]

        # Act & Assert
        for method in unsupported_methods:
            response = method('/api/config')

            # Assert - Should return 405 Method Not Allowed
            assert response.status_code == 405


class TestResponseHelpers:
    """
    Test the helper functions for API responses
    - `success_response`: Helper for successful responses
    - `error_response`: Helper for error responses
    """

    def test_error_response_default_status(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test error_response with default status code

        Expects:
            400 Bad Request
            JSON response with 'result' and 'message' keys

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act - We need to be within the Flask app context
        with client.application.app_context():
            response = error_response("Test error message")

            # Assert - Should return 400 Bad Request
            assert response.status_code == 400

            # Assert - Response should be JSON with expected structure
            data = json.loads(response.data)
            assert data['result'] == 'error'
            assert data['message'] == 'Test error message'

    def test_error_response_custom_status(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test error_response with custom status code

        Expects:
            404 Not Found
            JSON response with 'result' and 'message' keys

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        with client.application.app_context():
            response = error_response("Not found", status=404)

            # Assert - Should return 404 Not Found
            assert response.status_code == 404

            # Assert - Response should be JSON with expected structure
            data = json.loads(response.data)
            assert data['result'] == 'error'
            assert data['message'] == 'Not found'

    def test_success_response_minimal(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test success_response with minimal parameters

        Expects:
            200 OK
            JSON response with 'result' key

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        with client.application.app_context():
            response = success_response()

            # Assert - Should return 200 OK
            assert response.status_code == 200

            # Assert - Response should be JSON with expected structure
            data = json.loads(response.data)
            assert data['result'] == 'success'
            assert 'message' not in data

    def test_success_response_with_message(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test success_response with message

        Expects:
            200 OK
            JSON response with 'result' and 'message' keys

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        with client.application.app_context():
            response = success_response("Operation completed")

            # Assert - Should return 200 OK
            assert response.status_code == 200

            # Assert - Response should be JSON with expected structure
            data = json.loads(response.data)
            assert data['result'] == 'success'
            assert data['message'] == 'Operation completed'

    def test_success_response_with_data(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test success_response with additional data

        Expects:
            200 OK
            JSON response with 'result' and 'config' keys

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Arrange
        test_data = {'config': {'key': 'value'}}

        # Act
        with client.application.app_context():
            response = success_response(data=test_data)

            # Assert - Should return 200 OK
            assert response.status_code == 200

            # Assert - Response should be JSON with expected structure
            data = json.loads(response.data)
            assert data['result'] == 'success'
            assert data['config'] == {'key': 'value'}

    def test_success_response_custom_status(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test success_response with custom status code

        Expects:
            201 Created
            JSON response with 'result' and 'message' keys

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Act
        with client.application.app_context():
            response = success_response("Created", status=201)

            # Assert - Should return 201 Created
            assert response.status_code == 201

            # Assert - Response should be JSON with expected structure
            data = json.loads(response.data)
            assert data['result'] == 'success'
            assert data['message'] == 'Created'

    def test_success_response_message_and_data(
        self,
        client: FlaskClient
    ) -> None:
        """
        Test success_response with both message and data

        Expects:
            200 OK
            JSON response with 'result', 'message', and 'data' keys

        Args:
            client (FlaskClient): The test client for making requests

        Returns:
            None
        """

        # Arrange
        test_data = {'user': 'john', 'id': 123}

        # Act
        with client.application.app_context():
            response = success_response("User created", data=test_data)

            # Assert - Should return 200 OK
            assert response.status_code == 200

            # Assert - Response should be JSON with expected structure
            data = json.loads(response.data)
            assert data['result'] == 'success'
            assert data['message'] == 'User created'
            assert data['user'] == 'john'
            assert data['id'] == 123
