#!/usr/bin/env python3
"""Calculate expected bearing and depth to the test boxes from Gazebo ground truth.

Usage: python3 expected_bearing.py ROBOT_X ROBOT_Y ROBOT_YAW
Read x, y, and yaw from `gz model -m waffle -p`.
"""
import math
import sys

CAM_FWD, CAM_LEFT = 0.064, -0.065
FACE_X = 0.4
BOXES = {"red": (0.5, -3.5), "green": (0.5, -4.0), "blue": (0.5, -4.5)}
HALF_FOV = math.degrees(math.atan(320.0 / 565.6))


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    try:
        rx, ry, yaw = map(float, sys.argv[1:4])
    except ValueError:
        print("Robot x, y, and yaw must be numeric values.", file=sys.stderr)
        return 2

    camera_x = rx + CAM_FWD * math.cos(yaw) - CAM_LEFT * math.sin(yaw)
    camera_y = ry + CAM_FWD * math.sin(yaw) + CAM_LEFT * math.cos(yaw)
    for name, (box_x, box_y) in BOXES.items():
        bearing = math.degrees(math.atan2(box_y - camera_y, box_x - camera_x) - yaw)
        bearing = (bearing + 180) % 360 - 180
        depth = (FACE_X - camera_x) * math.cos(yaw) + (box_y - camera_y) * math.sin(yaw)
        visible = "in view" if abs(bearing) < HALF_FOV and depth > 0 else "OUT of view"
        print(f"{name:5s} expected bearing={bearing:+6.1f} deg   depth={depth:4.2f} m   {visible}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
