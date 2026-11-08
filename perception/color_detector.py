#!/usr/bin/env python3
"""Detect red, green, and blue boxes in the TurtleBot3 camera stream.

Subscribes to /camera/image_raw and publishes:
  /perception/annotated   annotated image (rgb8)
  /perception/detections  JSON string containing bearing, distance, and area

Bearing is positive when the object is left of the image centre, following the
ROS convention. Distance uses the known 0.3 m box height and is null when the
box is clipped by the top or bottom of the image.
"""
import json
import math

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import String

COLORS = {
    "red": [((0, 200, 70), (5, 255, 255)), ((175, 200, 70), (179, 255, 255))],
    "green": [((40, 120, 70), (80, 255, 255))],
    "blue": [((100, 120, 70), (130, 255, 255))],
}
DRAW = {"red": (0, 0, 255), "green": (0, 255, 0), "blue": (255, 0, 0)}
MIN_AREA = 800
BOX_HEIGHT_M = 0.3


class ColorDetector(Node):
    def __init__(self):
        super().__init__("color_detector")
        self.fx, self.cx = 565.6, 320.5
        qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(CameraInfo, "/camera/camera_info", self.on_info, qos)
        self.create_subscription(Image, "/camera/image_raw", self.on_image, qos)
        self.pub = self.create_publisher(Image, "/perception/annotated", qos)
        self.det_pub = self.create_publisher(String, "/perception/detections", 10)
        self.last_log = self.get_clock().now()
        self.last_save = self.get_clock().now()

    def on_info(self, msg: CameraInfo):
        self.fx, self.cx = msg.k[0], msg.k[2]

    def on_image(self, msg: Image):
        rgb = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        out = bgr.copy()
        lines = []
        detections = {}

        for name, ranges in COLORS.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lo, hi in ranges:
                mask |= cv2.inRange(hsv, np.array(lo), np.array(hi))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:1]
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < MIN_AREA:
                    continue
                x, y, w, h = cv2.boundingRect(contour)
                moments = cv2.moments(contour)
                cx_px = moments["m10"] / moments["m00"]
                cy_px = moments["m01"] / moments["m00"]
                bearing = math.degrees(math.atan2(self.cx - cx_px, self.fx))
                truncated = y <= 1 or y + h >= msg.height - 1
                distance = None if truncated else self.fx * BOX_HEIGHT_M / h
                detections[name] = {
                    "bearing_deg": round(bearing, 2),
                    "dist_m": None if distance is None else round(distance, 3),
                    "area": int(area),
                }
                label = "n/a" if distance is None else f"{distance:.1f}m"
                cv2.rectangle(out, (x, y), (x + w, y + h), DRAW[name], 2)
                cv2.putText(
                    out,
                    f"{name} {label} {bearing:+.0f}deg",
                    (x, max(y - 6, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    DRAW[name],
                    1,
                )
                lines.append(
                    f"{name:5s} centroid=({cx_px:5.0f},{cy_px:4.0f}) "
                    f"area={area:6.0f} bearing={bearing:+6.1f} deg "
                    f"dist~{distance if distance is not None else float('nan'):4.2f} m"
                )

        self.det_pub.publish(String(data=json.dumps({"detections": detections})))

        now = self.get_clock().now()
        if (now - self.last_log).nanoseconds > 5e8:
            self.last_log = now
            print("\n".join(lines) if lines else "no detections")
            print("-" * 60)
        if (now - self.last_save).nanoseconds > 5e9:
            self.last_save = now
            cv2.imwrite("/tmp/detections.png", out)

        annotated = Image()
        annotated.header = msg.header
        annotated.height, annotated.width = out.shape[:2]
        annotated.encoding = "rgb8"
        annotated.step = annotated.width * 3
        annotated.data = cv2.cvtColor(out, cv2.COLOR_BGR2RGB).tobytes()
        self.pub.publish(annotated)


def main():
    rclpy.init()
    node = ColorDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
