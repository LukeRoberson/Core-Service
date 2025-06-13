# Use the custom base image
FROM lukerobertson19/base-os:latest

LABEL org.opencontainers.image.title="AI Assistant Core Service"
LABEL org.opencontainers.image.description="The core service, which manages configuration, plugins, and Docker integration."
LABEL org.opencontainers.image.base.name="lukerobertson19/base-os:latest"
LABEL org.opencontainers.image.source="https://github.com/LukeRoberson/Core-Service"
LABEL org.opencontainers.image.version="1.0.0"

# The health check URL for the service
LABEL net.networkdirection.healthz="http://localhost:5100/api/health"

# The name of the service, as it should appear in the compose file
LABEL net.networkdirection.service.name="core"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Start the application using uWSGI
CMD ["uwsgi", "--ini", "uwsgi.ini"]
