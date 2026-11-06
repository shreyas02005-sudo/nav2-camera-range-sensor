#!/usr/bin/env bash
# Kill leftover Gazebo / ROS processes before a fresh launch.
# Stale gzserver or gzclient processes from a previous session are a common
# reason for Gazebo failing to start on the second attempt.

pkill -9 gzserver 2>/dev/null
pkill -9 gzclient 2>/dev/null
pkill -f static_transform_publisher 2>/dev/null
pkill -f nav2_container 2>/dev/null
pkill -f rviz2 2>/dev/null
pkill -f robot_state_publisher 2>/dev/null
ros2 daemon stop 2>/dev/null
sleep 2

echo "Remaining Gazebo/ROS processes:"
ps aux | grep -E "gzserver|gzclient|rviz2|component_container" | grep -v grep || echo "none"
