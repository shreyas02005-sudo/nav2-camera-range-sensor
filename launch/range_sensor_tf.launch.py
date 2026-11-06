"""Publish the static transform for the front range sensor.

The TurtleBot3 URDF used by robot_state_publisher does not contain the range
link that was added to the Gazebo model, so the transform has to be published
separately. The offsets match the <pose> in models/front_range_sensor.sdf.xml.

Run with:
    ros2 launch launch/range_sensor_tf.launch.py
"""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="front_range_tf",
                arguments=[
                    "--x", "0.08", "--y", "0", "--z", "0.04",
                    "--roll", "0", "--pitch", "0", "--yaw", "0",
                    "--frame-id", "base_link",
                    "--child-frame-id", "front_range_link",
                ],
            )
        ]
    )
