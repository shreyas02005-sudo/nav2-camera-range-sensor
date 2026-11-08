#!/usr/bin/env python3
"""Turn toward a coloured box and drive up to it.

Usage:
    python3 color_follower.py green
    python3 color_follower.py red 0.6

Close teleop and Nav2 before starting: another /cmd_vel publisher will
conflict with this controller.
"""
import json
import math
import sys

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String

K_ANG = 1.2
MAX_ANG = 0.8
SEARCH_ANG = 0.4
MAX_LIN = 0.15
MIN_LIN = 0.03
K_LIN = 0.5
TURN_FIRST_DEG = 15.0
DEADBAND_DEG = 1.0
RESUME_MARGIN = 0.15
STALE_S = 0.5


def compute_cmd(state, bearing_deg, dist_m, stop_dist, last_sign):
    """Return linear speed, angular speed, and the updated tracking state."""
    angular = 0.0
    if abs(bearing_deg) > DEADBAND_DEG:
        angular = max(-MAX_ANG, min(MAX_ANG, K_ANG * math.radians(bearing_deg)))

    if dist_m is None:
        if abs(bearing_deg) < 10.0:
            return 0.0, 0.0, "DONE"
        return 0.0, angular, state

    limit = stop_dist + (RESUME_MARGIN if state == "DONE" else 0.0)
    if dist_m <= limit:
        return 0.0, 0.0, "DONE"

    if abs(bearing_deg) > TURN_FIRST_DEG:
        return 0.0, angular, "TRACK"
    linear = max(MIN_LIN, min(MAX_LIN, K_LIN * (dist_m - stop_dist)))
    return linear, angular, "TRACK"


class ColorFollower(Node):
    def __init__(self, color, stop_dist):
        super().__init__("color_follower")
        self.color, self.stop_dist = color, stop_dist
        self.state = "TRACK"
        self.last = None
        self.last_sign = 1.0
        self.mode = None
        self.create_subscription(String, "/perception/detections", self.on_detection, 10)
        self.cmd = self.create_publisher(Twist, "/cmd_vel", 10)
        self.create_timer(0.1, self.step)
        self.get_logger().info(f"Following '{color}', stopping at {stop_dist:.2f} m")

    def now_s(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def on_detection(self, msg):
        detection = json.loads(msg.data).get("detections", {}).get(self.color)
        if detection:
            self.last = (self.now_s(), detection["bearing_deg"], detection["dist_m"])
            self.last_sign = 1.0 if detection["bearing_deg"] >= 0 else -1.0

    def set_mode(self, mode):
        if mode != self.mode:
            self.mode = mode
            self.get_logger().info(mode)

    def step(self):
        command = Twist()
        fresh = self.last is not None and (self.now_s() - self.last[0]) < STALE_S
        if not fresh:
            self.set_mode(f"{self.color} not visible: searching")
            command.angular.z = SEARCH_ANG * self.last_sign
        else:
            _, bearing, distance = self.last
            linear, angular, self.state = compute_cmd(
                self.state, bearing, distance, self.stop_dist, self.last_sign
            )
            command.linear.x, command.angular.z = linear, angular
            self.set_mode("arrived" if self.state == "DONE" else "tracking")
        self.cmd.publish(command)

    def stop(self):
        for _ in range(3):
            self.cmd.publish(Twist())


def main():
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in ("red", "green", "blue"):
        print(__doc__)
        return 2
    color = sys.argv[1]
    try:
        stop_dist = float(sys.argv[2]) if len(sys.argv) == 3 else 0.5
    except ValueError:
        print("Stop distance must be a number in metres.", file=sys.stderr)
        return 2
    if stop_dist < 0:
        print("Stop distance must not be negative.", file=sys.stderr)
        return 2

    try:
        from rclpy.signals import SignalHandlerOptions
        rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    except (ImportError, TypeError):
        rclpy.init()
    node = ColorFollower(color, stop_dist)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
