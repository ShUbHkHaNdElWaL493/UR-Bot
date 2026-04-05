#!/bin/bash
set -e

source "/opt/ros/humble/setup.bash"
colcon build --packages-select ur_robot_msgs
source "install/setup.bash"
colcon build

exec "$@"