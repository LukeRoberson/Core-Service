# Core Service

The core service manages any core functionality for the app as a whole. The exception is specialised functionality like security or logging.

This includes:
* Managing global configuration
* Registing plugins
* Managing plugins
* Docker communication
</br></br>


> [!NOTE]  
> Additional documentation can be found in the **docs** folder
</br></br>


----
# Project Organization
## Python Files

| File          | Provided Function                                             |
| ------------- | ------------------------------------------------------------- |
| main.py       | Entry point to the service, load configuration, set up routes |
| api.py        | API endpoints for this service                                |
| config.py     | Manage the configuration of the entire application            |
| plugins.py    | Manage plugins                                                |
| docker_api.py | Get information about containers running in Docker            |
| systemlog.py  | Send logging information to the logging service               |
</br></br>



----
# Configuration Management

The Core service manages the configuration for the entire application. Other services may request configuration information from this service through the API.

Configuration is stored in **config/global.yaml**. It can be edited directly, or through the 'configuration' page of the web interface. Any changes in the web interface will update the YAML file.

The config file contains sensitive information, so it should be passed to the container at runtime, not included in the Docker image.

The **GlobalConfig** class in **config.py** is responsible for reading, maintaining, and updating the configuration.

</br></br>


----
# Plugin Management
The Core service manages plugins. This means registering new plugins, and loading plugins at runtime. Other services can request plugin information through the API.

Configuration is stored in **config/plugins.yaml**. It can be edited directly, or through the 'plugins' page of the web interface. Any changes in the web interface will update the YAML file.

The plugins file contains sensitive information, so it should be passed to the container at runtime, not included in the Docker image.

The **PluginConfig** class in **plugins.py** is responsible for reading, maintaining, and updating the configuration.
</br></br>


----
# Docker Interaction

Application services run as containers in Docker. The Core service can retrieve information about these containers from the Docker host.

> [!NOTE]  
> Only a single Docker host is supported at this time. This service would need to be extended to support a Swarm or Kubernetes cluster.

The Docker host has to be configured to allow remote connections. This is in the **/lib/systemd/system/docker.service** file on the host.

The **DockerApi** class in the **docker_api.py** file manages interactions with the Docker host.

Other services can request container status from the Core service using the API. This is typically only the web interface, which displays the status on the _about_ page.
</br></br>


