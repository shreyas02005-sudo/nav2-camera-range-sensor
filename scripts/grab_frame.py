#!/usr/bin/env python3
"""Grab one frame from /camera/image_raw, print pixel statistics, save a PNG.

Useful for checking the camera pipeline without a GUI viewer: a mean close to
zero means the image is black. Uses a reliable QoS subscription, matching the
Gazebo camera plugin.

Usage:
    python3 grab_frame.py [output.png]
"""
import sys

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image


class GrabFrame(Node):
    def __init__(self, out_path: str):
        super().__init__("grab_frame")
        self.out_path = out_path
        qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(Image, "/camera/image_raw", self.on_image, qos)

    def on_image(self, msg: Image) -> None:
        img = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
        print(
            f"{msg.encoding} {msg.width}x{msg.height}  "
            f"min={img.min()} max={img.max()} mean={img.mean():.1f}"
        )
        try:
            import cv2

            cv2.imwrite(self.out_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            print(f"Saved {self.out_path}")
        except ImportError:
            print("OpenCV not installed; skipping PNG export.")
        raise SystemExit


def main() -> None:
    rclpy.init()
    node = GrabFrame(sys.argv[1] if len(sys.argv) > 1 else "/tmp/frame.png")
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
