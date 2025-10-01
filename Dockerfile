# Use the custom base image
FROM lukerobertson19/base-os:latest

LABEL org.opencontainers.image.title="AI Assistant Core Service"
LABEL org.opencontainers.image.description="The core service, which manages configuration, plugins, and Docker integration."
LABEL org.opencontainers.image.base.name="lukerobertson19/base-os:latest"
LABEL org.opencontainers.image.source="https://github.com/LukeRoberson/Core-Service"

# The health check URL for the service
LABEL net.networkdirection.healthz="http://localhost:5100/api/health"

# The name of the service, as it should appear in the compose file
LABEL net.networkdirection.service.name="core"

# Stay as root for setup operations
USER root

# Install shadow package for user management (if not already in base image)
RUN apk add --no-cache shadow su-exec dos2unix

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Copy the entrypoint script, convert line endings, and set permissions
COPY docker_entrypoint.sh /usr/local/bin/docker_entrypoint.sh
RUN dos2unix /usr/local/bin/docker_entrypoint.sh && \
    chmod +x /usr/local/bin/docker_entrypoint.sh && \
    ls -la /usr/local/bin/docker_entrypoint.sh

# Copy the rest of the application code
COPY . .

# Ensure appuser owns the application files
RUN chown -R appuser:appgroup /app

# Switch to appuser to install Python dependencies in user space
USER appuser

# Install dependencies as appuser
RUN pip install --upgrade pip && pip install -r requirements.txt

# Add user pip packages to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Switch back to root for entrypoint execution
USER root

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/docker_entrypoint.sh"]

# Start the application using uWSGI
CMD ["uwsgi", "--ini", "uwsgi.ini"]

# Set the version of the image in metadata
ARG VERSION
LABEL org.opencontainers.image.version="${VERSION}"