#!/usr/bin/env bash
# Spawn the static colour test boxes at their original Gazebo world positions.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ros2 run gazebo_ros spawn_entity.py -entity box_red \
  -file "$DIR/models/box_red.sdf" -x 0.5 -y -3.5 -z 0.15
ros2 run gazebo_ros spawn_entity.py -entity box_green \
  -file "$DIR/models/box_green.sdf" -x 0.5 -y -4.0 -z 0.15
ros2 run gazebo_ros spawn_entity.py -entity box_blue \
  -file "$DIR/models/box_blue.sdf" -x 0.5 -y -4.5 -z 0.15
