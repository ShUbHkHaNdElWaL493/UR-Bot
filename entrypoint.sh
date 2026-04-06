#!/bin/bash
set -e

# Source the main ROS 2 Humble setup
source "/opt/ros/humble/setup.bash"

# Source your specific workspace if it exists
if [ -f "/ur_robot/install/setup.bash" ]; then
  source "/ur_robot/install/setup.bash"
fi

exec "$@"