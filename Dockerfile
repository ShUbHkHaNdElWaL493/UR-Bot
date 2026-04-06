FROM osrf/ros:humble-desktop

RUN apt-get update && apt-get install -y \
    ros-humble-turtlesim \
    ros-humble-desktop \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ur_robot

RUN chmod +x entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]