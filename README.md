# Core Service

The core service manages any core functionality for the app as a whole. The exception is specialised functionality like security or logging.

This includes:
* Managing global configuration
* Registing plugins
* Managing plugins


</br></br>
----

# Project Organization
## Python Files

| File         | Provided Function                                             |
| ------------ | ------------------------------------------------------------- |
| main.py      | Entry point to the service, load configuration, set up routes |


## Other Files

| File             | Description                                         |
| ---------------- | --------------------------------------------------- |
| .dockerignore    | Files that are excluded from the container image    |
| .gitignore       | Files that are excluded from git                    |
| Dockerfile       | For building the image                              |
| requirements.txt | Python modules and versions to install in the image |



</br></br>
----

# API

There is an API in place so other services can access security functions.

| Endpoint           | Methods | Description                          |
| ------------------ | ------- | ------------------------------------ |
| /api/health        | GET     | Check the health of the container    |
</br></br>


## Responses

Unless otherwise specified, all endpoints have a standard JSON response, including a '200 OK' message if everything is successful.

A successful response:
```
{
    'result': 'success'
}
```

An error:
```
{
    'result': 'error',
    'error': 'A description of the error'
}
```
</br></br>


## Health

Docker uses this endpoint to check the health of the container. If all is ok, this will respond with a '200 OK'
</br></br>
