#!/usr/bin/env python3
"""Reduce the cost of the TurtleBot3 waffle camera in Gazebo.

The stock waffle model renders a 1920x1080 image at 30 Hz with a 300 m far
clip. Under WSL2 that is heavy enough that frames stop reaching ROS. This
script rewrites only the camera sensor block of the model file to
640x480 at 10 Hz with a 10 m far clip.

Usage:
    python3 configure_camera.py [path/to/model.sdf]
"""
import re
import shutil
import sys
from pathlib import Path

DEFAULT_MODEL = (
    Path.home()
    / "turtlebot3_ws/src/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf"
)

WIDTH, HEIGHT, RATE, FAR = 640, 480, 10, 10


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MODEL
    text = path.read_text()

    start = text.find('<sensor name="camera" type="camera">')
    if start == -1:
        print("Camera sensor block not found; nothing changed.")
        return 1
    end = text.find("</sensor>", start)
    block = text[start:end]

    new_block = re.sub(r"<width>\d+</width>", f"<width>{WIDTH}</width>", block)
    new_block = re.sub(r"<height>\d+</height>", f"<height>{HEIGHT}</height>", new_block)
    new_block = re.sub(
        r"<update_rate>[\d.]+</update_rate>", f"<update_rate>{RATE}</update_rate>", new_block
    )
    new_block = re.sub(r"<far>[\d.]+</far>", f"<far>{FAR}</far>", new_block)

    if new_block == block:
        print("Camera block already matches the target settings.")
        return 0

    shutil.copy(path, path.with_suffix(".sdf.bak"))
    path.write_text(text[:start] + new_block + text[end:])
    print(f"Updated {path} (backup: {path.with_suffix('.sdf.bak').name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
