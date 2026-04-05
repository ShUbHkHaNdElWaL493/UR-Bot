# Use the official ROS 2 Humble image
FROM osrf/ros:humble-desktop

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    ros-humble-turtlesim \
    ~nros-humble-desktop \
    && rm -rf /var/lib/apt/lists/*

# Set up the workspace
WORKDIR /ur_robot

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["entrypoint.sh"]