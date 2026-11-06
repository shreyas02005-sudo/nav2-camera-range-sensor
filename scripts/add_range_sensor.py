#!/usr/bin/env python3
"""Insert the front range sensor into the TurtleBot3 waffle model.

The block that gets inserted is the same one kept for reference in
models/front_range_sensor.sdf.xml.

Usage:
    python3 add_range_sensor.py [path/to/model.sdf]
"""
import shutil
import sys
from pathlib import Path

DEFAULT_MODEL = (
    Path.home()
    / "turtlebot3_ws/src/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf"
)
SENSOR_FILE = Path(__file__).resolve().parent.parent / "models" / "front_range_sensor.sdf.xml"


def main() -> int:
    model = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MODEL
    text = model.read_text()

    if "front_range_link" in text:
        print("Range sensor already present; nothing changed.")
        return 0

    block = SENSOR_FILE.read_text()
    # Drop the leading XML comment so the model file stays tidy.
    block = block[block.index("<link"):]

    close = text.rindex("</model>")
    shutil.copy(model, model.with_suffix(".sdf.bak2"))
    model.write_text(text[:close] + "\n" + block + "\n" + text[close:])
    print(f"Added front range sensor to {model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
