# AI Assistant

The AI assistant is a chatbot that integrates with parts of the network to provide information.

This is a microservice architecture, where services are deployed as Docker containers.

## Core Service

This repository is for the core service. This provides:
* Configuration management for the entire application
* Plugin management for the entire application
* API calls to the Docker host to get container status
* API endpoints for communication between containers

## Backend

- The backend is written in python
- Flask provides the API
- YAML files contain configuration for the app

## Code Standards

- Use good variable names, avoiding abbreviations and single letter variables
- Use snake_casing for Python
- Use type hints in all languages which support them

## Project Structure

- The root folder contains python code
- `docs` contains project documentation
- `config` contains sample configuration files
- `tests` contains unit testing files
