FROM ubuntu:26.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8

# This is an auto generated Dockerfile for ros:perception
# generated from docker_images_ros2/create_ros_image.Dockerfile.em
FROM ros:lyrical-ros-base-resolute

# install ros2 packages
RUN apt-get update && apt-get install -y locales software-properties-common curl \
    && locale-gen en_US en_US.UTF-8 \
    && add-apt-repository universe -y \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu resolute main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null \
    && apt-get update && apt-get install -y --no-install-recommends \
    ros-lyrical-desktop \
    ros-lyrical-ros-gz \
    ros-lyrical-gz-ros2-control \
    ros-lyrical-ros2-control \
    ros-lyrical-ros2-controllers \
    ros-lyrical-xacro \
    ros-lyrical-perception \
    python3-colcon-common-extensions \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

    ARG USERNAME=ubuntu
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME \
    && apt-get update && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
RUN echo "source /opt/ros/lyrical/setup.bash" >> ~/.bashrc