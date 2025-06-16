# Core Service

The core service manages any core functionality for the app as a whole. The exception is specialised functionality like security or logging.

This includes:
* Managing global configuration
* Registing plugins
* Managing plugins
* Docker communication
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
# API

There is an API in place so other services can access security functions.

| Endpoint           | Methods    | Description                              |
| ------------------ | ---------- | ---------------------------------------- |
| /api/health        | GET        | Check the health of the container        |
| /api/config        | GET, PATCH | Retrieve and update global configuration |
| /api/plugins       | GET        | Get information about plugins            |
| /api/containers    | GET        | Get information about running containers |
</br></br>


## Responses

Unless otherwise specified, all endpoints have a standard JSON response, including a '200 OK' message if everything is successful.

A successful response:
```json
{
    'result': 'success'
}
```

An error:
```json
{
    'result': 'error',
    'error': 'A description of the error'
}
```
</br></br>


### Health

This is for checking that Flask is responding from the localhost, so Docker can see if this is up.

This just returns a '200 OK' response.


### Config and Plugins

When collecting configuration information with a GET request, a _result_ will be sent, along with the configuration information.

```json
{
    "result": "success",
    "config": "<CONFIG DATA: Dict>"
}
```
</br></br>

Plugin information is returned in a similar format, but it is a list of config:
```json
{
    "result": "success",
    "config": "<PLUGIN DATA: List[Dict]>"
}
```
</br></br>


### Containers

This returns the status of the containers in Docker, that represent the services in this application.

This is a list of containers and their status.

```json
{
    "result": "success",
    "services": "<CONTAINERS: List[Dict]>"
}
```
</br></br>


The container details are in this format:

```python
details = {
    'name': <SERVICE NAME>,
    'title': <CONTAINER TITLE>,
    'description': <CONTAINER DESCRIPTION>,
    'service_name': <SERVICE NAME>,
    'version': <IMAGE VERSION>,
    'status': <CONTAINER VERSION>,
    'health': <HEALTH STATUS>,
}
```


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


