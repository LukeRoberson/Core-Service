#!/bin/sh

# Function to handle Docker socket permissions
setup_docker_socket_permissions() {
    # Check if docker socket is mounted and accessible
    if [ -S /var/run/docker.sock ]; then
        echo "Docker socket detected, setting up permissions..."
        
        # Get the group ID of the mounted docker socket
        docker_socket_group_id=$(stat -c '%g' /var/run/docker.sock)
        echo "Docker socket group ID: ${docker_socket_group_id}"
        
        # Check if a group with this GID already exists
        existing_group_name=$(getent group ${docker_socket_group_id} 2>/dev/null | cut -d: -f1)
        
        if [ -n "${existing_group_name}" ]; then
            echo "Group ${existing_group_name} (GID: ${docker_socket_group_id}) already exists"
            docker_group_name="${existing_group_name}"
        else
            # Create new group with the correct GID
            docker_group_name="docker_runtime"
            addgroup --system --gid ${docker_socket_group_id} ${docker_group_name}
            echo "Created group ${docker_group_name} with GID ${docker_socket_group_id}"
        fi
        
        # Add appuser to the docker group
        adduser appuser ${docker_group_name}
        echo "Added appuser to group: ${docker_group_name}"
        
        # Verify the setup
        user_groups=$(groups appuser)
        echo "User appuser is now in groups: ${user_groups}"
    else
        echo "Docker socket not mounted, skipping Docker permission setup"
    fi
}

# Set up Docker socket permissions if needed
setup_docker_socket_permissions

# Switch to appuser and execute the main command
echo "Starting application as appuser..."
exec su-exec appuser "$@"
