FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    ros-humble-robotiq* \
    ros-humble-ur \
    ros-humble-ur-* \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ur_robot
COPY ./src ./src

RUN source /opt/ros/humble/setup.bash && colcon build
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo "source /ur_robot/install/setup.bash" >> ~/.bashrc

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["bash"]