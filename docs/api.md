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

