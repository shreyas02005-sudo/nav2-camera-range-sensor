#!/usr/bin/env python3
"""Convert a point from the Nav2 map frame to Gazebo world coordinates.

The map and the Gazebo world differ by a constant shift in this setup (the map
was built with SLAM starting at the robot's spawn point). Measure the shift once
with the robot localised:

    offset = gazebo_pose - amcl_pose

then use this script to place objects where you clicked on the map.

Usage:
    python3 map_to_gazebo.py MAP_X MAP_Y OFFSET_X OFFSET_Y
"""
import sys

if len(sys.argv) != 5:
    print(__doc__)
    sys.exit(2)

map_x, map_y, off_x, off_y = map(float, sys.argv[1:])
print(f"gazebo x={map_x + off_x:.2f} y={map_y + off_y:.2f}")
