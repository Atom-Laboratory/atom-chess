FROM tiryoh/ros2-desktop-vnc:lyrical

ENV DEBIAN_FRONTEND=noninteractive

# This is an auto generated Dockerfile for ros:perception
# generated from docker_images_ros2/create_ros_image.Dockerfile.em
FROM ros:lyrical-ros-base-resolute

# install ros2 packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-lyrical-ros-gz \
    ros-lyrical-gz-ros2-control \
    ros-lyrical-ros2-control \
    ros-lyrical-ros2-controllers \
    ros-lyrical-xacro \
    ros-lyrical-perception \
    python3-colcon-common-extensions \
    nano \
    htop \
    && rm -rf /var/lib/apt/lists/*

# USER ubuntu
WORKDIR /home/ubuntu/simulation

RUN echo "source /opt/ros/humble/setup.bash" >> /home/ubuntu/.bashrc

RUN echo "if [ -f /home/ubuntu/simulation/install/setup.bash ]; then source /home/ubuntu/simulation/install/setup.bash; fi" >> /home/ubuntu/.bashrc