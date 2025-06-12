"""
Module: docker_api.py

Connects to a docker instance, and retrieves information
    about the running containers.

Need to enable remote connections to the Docker daemon:
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

import docker
from docker.models.images import Image


# Assume the Docker server is running on the host machine
DOCKER_SERVER = "host.docker.internal"


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
        server: str = DOCKER_SERVER,
        port: int = 2375
    ) -> None:
        """
        Initializes the DockerApi instance.

        Args:
            server (str): The Docker server address.
            port (int): The port to connect to the Docker daemon.
                Default is 2375.

        Returns:
            None
        """

        self.client: docker.DockerClient = docker.DockerClient(
            base_url=f'tcp://{server}:{port}',
        )

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

            if service_label == service_name:
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
            # Skip images without tags
            if not image.tags:
                continue

            # Skip images with no labels
            if not image.labels:
                continue

            # Skip images that do not have a service name (custom label)
            service_name = image.labels.get(
                "net.networkdirection.service.name",
                "Unknown Service"
            )
            if service_name == "Unknown Service":
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
            print(f"Tags: {', '.join(image.tags)}")

            print(f"Title: {title}")
            print(f"Description: {description}")
            print(f"Service Name: {service_name}")
            print(f"Version: {version}")

            print("-" * 40)

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
