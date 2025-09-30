"""
Module: docker_api.py

Connects to a docker instance, and retrieves information
    about the running containers.

Tries to connect via the docker socket first, then falls back to TCP.
    If neither method works, raises a ConnectionError.

If using a compose file, mount the docker socket:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

Can override the connection method via the environment variable
    in the compose file:
        DOCKER_CONNECTION_METHOD=socket  # Forces socket connection
        DOCKER_CONNECTION_METHOD=tcp     # Forces TCP connection
        DOCKER_CONNECTION_METHOD=auto    # Uses default behavior

To enable the Docker API over the unix socket, ensure the user
    is in the 'docker' group:
        sudo usermod -aG docker $USER

To enable the Docker API over TCP on Linux:
    1. Edit /lib/systemd/system/docker.service
    2. Find the line starting with 'ExecStart'
    3. Add this to the line: '-H=tcp://0.0.0.0:2375'
    4. Save and exit
    5. Reload the docker daemon: 'systemctl daemon-reload'
    6. Restart the container service: 'sudo service docker restart'
    7. Test with: 'curl http://localhost:2375/images/json'

Need to make sure that 'host.docker.internal' resolves to the Docker host
    This means updating the compose file to include the following:
        extra_hosts:
            - host.docker.internal: host-gateway

Standardised labels (OCI) for Docker images:
    org.opencontainers.image.version:       Version of the image.
    org.opencontainers.image.title:         Short title for the image.
    org.opencontainers.image.description:   Detailed description of the image.

Requirements:
    docker - The Docker SDK for Python.
        Note: On Windows, this uses the 'pywin32' package.
            This shoule be removed from requirements.txt
    colorama - For colored terminal text output.
"""

# Docker SDK for Python
import docker
from docker.models.images import Image
from docker.errors import DockerException

# Standard library imports
import logging
import os
import platform


# Docker socket paths
DOCKER_SOCKET_UNIX = "/var/run/docker.sock"
DOCKER_SOCKET_WINDOWS = "npipe://./pipe/docker_engine"
DOCKER_SERVER_FALLBACK = "host.docker.internal"


class DockerApi:
    """
    A class to interact with the Docker API.
    Provides methods to list containers, list images, and pull images.

    Attributes:
        server (str): The Docker server address.
        client (docker.DockerClient): The Docker client instance.
    """

    def __init__(
        self,
        server: str = DOCKER_SERVER_FALLBACK,
        port: int = 2375,
        timeout: int = 10,
        force_tcp: bool = False
    ) -> None:
        """
        Initializes the DockerApi instance.

        Args:
            server (str): The Docker server address (fallback for TCP).
            port (int): The port to connect to the Docker daemon.
                Default is 2375.
            timeout (int): The timeout for the connection in seconds.
                Default is 10 seconds.
            force_tcp (bool): Force the use of TCP connection instead of
                Unix socket. Default is False.

        Raises:
            ConnectionError: If the Docker server is not reachable.

        Returns:
            None
        """

        self.server = server
        self.port = port
        self.timeout = timeout
        self.connection_method = None

        # Check for environment variable override
        docker_connection_method = os.getenv(
            'DOCKER_CONNECTION_METHOD',
            'auto'
        ).lower()
        print(
            f"DOCKER_CONNECTION_METHOD is set to: {docker_connection_method}"
        )

        # Override force_tcp based on environment variable
        if docker_connection_method == 'tcp':
            force_tcp = True
        elif docker_connection_method == 'socket':
            force_tcp = False

        # Get a list of ways to connect, in order of preference
        connection_attempts = self._get_connection_attempts(force_tcp)
        last_exception = None

        # Try each connection method until one succeeds
        for attempt in connection_attempts:
            print(
                f"Attempting to connect to Docker daemon via "
                f"{attempt['method']} at {attempt['url']}"
            )

            try:
                self.client: docker.DockerClient = docker.DockerClient(
                    base_url=attempt['url'],
                    timeout=timeout
                )

                # Test the connection
                self.client.ping()
                self.connection_method = attempt['method']
                logging.info(
                    f"Connected to Docker daemon via {self.connection_method}"
                )
                return

            except DockerException as docker_error:
                logging.error(
                    f"Failed to connect via {attempt['method']}: "
                    f"{docker_error}"
                )
                last_exception = docker_error
                continue

            except Exception as general_error:
                logging.error(
                    f"Failed to connect via {attempt['method']}: "
                    f"{general_error}"
                )
                last_exception = general_error
                continue

        # If all attempts failed
        logging.error(
            "Failed to connect to Docker daemon using all available methods"
        )
        raise ConnectionError(
            "Unable to connect to Docker daemon. "
            "Ensure Docker is running and accessible via socket or TCP."
        ) from last_exception

    def __enter__(
        self
    ) -> 'DockerApi':
        """
        Enter the runtime context related to this object.

        Returns:
            DockerApi: The instance of the DockerApi class.
        """

        return self

    def __exit__(
        self,
        exc_type: type,
        exc_value: Exception,
        traceback: object
    ) -> None:
        """
        Exit the runtime context related to this object.

        Args:
            exc_type (type): The exception type.
            exc_value (Exception): The exception value.
            traceback (object): The traceback object.

        Returns:
            None
        """

        self.client.close()

    def _get_connection_attempts(self, force_tcp: bool) -> list[dict]:
        """
        Get list of connection attempts in order of preference.

        Args:
            force_tcp (bool): Whether to force TCP connection.

        Returns:
            list[dict]: List of connection attempt configurations.
        """

        attempts = []

        if not force_tcp:
            # Try Unix socket first (Linux/macOS)
            if (
                platform.system() != "Windows" and
                os.path.exists(DOCKER_SOCKET_UNIX)
            ):
                attempts.append({
                    'url': f'unix://{DOCKER_SOCKET_UNIX}',
                    'method': 'Unix socket'
                })

            # Try Windows named pipe
            elif platform.system() == "Windows":
                attempts.append({
                    'url': DOCKER_SOCKET_WINDOWS,
                    'method': 'Windows named pipe'
                })

        # Fallback to TCP connections
        attempts.extend([
            {
                'url': f'tcp://{self.server}:{self.port}',
                'method': f'TCP ({self.server}:{self.port})'
            },
            {
                'url': 'tcp://localhost:2375',
                'method': 'TCP (localhost:2375)'
            },
            {
                'url': 'tcp://127.0.0.1:2375',
                'method': 'TCP (127.0.0.1:2375)'
            }
        ])

        return attempts

    def container_status(
        self,
        service_name: str,
    ) -> dict | None:
        """
        Get the details and status of a given container.

        Args:
            service_name (str): The service name of the container.
                This is assigned to the container via a custom label
                'net.networkdirection.service.name'.

        Returns:
            dict:
                A dict containing the container information.
                If the container is not found, returns None
        """

        status = {}
        containers = self.client.containers.list()
        if not containers:
            return None

        for container in containers:
            service_label = container.image.labels.get(
                "net.networkdirection.service.name",
                "Unknown Service"
            )
            plugin_label = container.image.labels.get(
                "net.networkdirection.plugin.name",
                "Unknown Plugin"
            )

            if service_label == service_name or plugin_label == service_name:
                # Get labels
                title = container.image.labels.get(
                    "org.opencontainers.image.title",
                    "Unknown Title"
                )
                description = container.image.labels.get(
                    "org.opencontainers.image.description",
                    "No description available"
                )
                version = container.image.labels.get(
                    "org.opencontainers.image.version",
                    "Unknown Version"
                )

                status = {
                    "name": container.name,
                    "title": title,
                    "description": description,
                    "service_name": service_name,
                    "version": version,
                    "status": container.status,
                    "health": container.health,
                }

        return status

    def list_images(
        self
    ) -> list[Image]:
        """
        List all Docker images on the server.

        Args:
            None

        Returns:
            list[Image]
                A list of Image objects representing Docker images.
        """

        images = []

        for image in self.client.images.list():
            logging.info(f"Processing image: {image.tags}")

            # Skip images without tags
            if not image.tags:
                continue

            # Skip images with no labels
            if not image.labels:
                continue

            # Skip images that do not have a service or plugin name
            service_name = image.labels.get(
                "net.networkdirection.service.name",
                "Unknown Service"
            )
            plugin_name = image.labels.get(
                "net.networkdirection.plugin.name",
                "Unknown Service"
            )
            if (
                service_name == "Unknown Service" and
                plugin_name == "Unknown Service"
            ):
                continue

            # Get additional label data
            title = image.labels.get(
                "org.opencontainers.image.title",
                "Unknown Title"
            )
            description = image.labels.get(
                "org.opencontainers.image.description",
                "No description available"
            )
            version = image.labels.get(
                "org.opencontainers.image.version",
                "Unknown Version"
            )

            # Print image information
            logging.info(f"Tags: {', '.join(image.tags)}")

            logging.info(f"Title: {title}")
            logging.info(f"Description: {description}")
            logging.info(f"Service Name: {service_name}")
            logging.info(f"Version: {version}")

            logging.info("-" * 40)

            # Append the image to the list
            images.append(image)

        return images

    def pull_images(
        self,
        image: Image
    ) -> None:
        """
        Pull a Docker image from the registry.

        Args:
            image (Image): The Docker image to pull.

        Returns:
            None
        """

        for line in self.client.api.pull(
            image.tags[0],
            stream=True,
            decode=True
        ):
            if 'Digest' not in line['status']:
                print(line['status'])
