# TurtleBot3 Nav2: Camera and Range Sensor Integration

Adding an RGB camera feed and a low-mounted range sensor to a TurtleBot3 Waffle in Gazebo Classic, wiring the range sensor into the Nav2 costmaps, and checking that it changes how the robot navigates.

The test is simple on purpose. An 8 cm tall box sits on the robot's route, below the height of the LiDAR scan. With the range sensor in the costmap, Nav2 plans around the box. Without it, the robot drives straight into it.

This builds on a separate SLAM and navigation setup: a custom Gazebo world, a Cartographer map and Nav2 navigation through it. If you want to reproduce this repository you need a working Nav2 setup of your own to run it on, as described under [Requirements](#requirements).

## Results

| Configuration | Obstacle in costmap | Outcome |
|---|---|---|
| Stock Nav2 parameters (LiDAR only) | No | Robot did not see the box and collided with it |
| Nav2 with the range sensor layer | Yes (local and global) | Planner routed around the box |

Recordings of both runs are in this [Google Drive folder](https://drive.google.com/drive/folders/1_qsFUcDb3oPudGYDkgD9RKODOBYeF5Z4?usp=sharing).

The camera feed from the robot in the simulated world, received over ROS 2 at 640x480:

![Camera view from the TurtleBot3 in Gazebo](docs/images/nav2_camera.jpeg)

These results come from a single obstacle layout in one world, repeated for the two configurations with the same start pose, goal and box position. It shows the mechanism working. It is not a statistical benchmark.

## What was built

**Camera.** The stock Waffle model already includes a camera, but it renders 1920x1080 at 30 Hz with a 300 m far clip, which is a lot to ask of a simulator running under WSL2. It is reduced to 640x480 at 10 Hz with a 10 m far clip, which is plenty for colour-based detection. It publishes `/camera/image_raw` and `/camera/camera_info`. Getting the images to actually arrive in ROS was a separate problem, solved by changing the DDS middleware (see below).

**Range sensor.** A narrow, five-ray sensor mounted at the front of the base, 4 cm above the base link origin. It publishes `sensor_msgs/Range` on `/front_range` with a 1.5 m maximum range and a 0.4 rad field of view. Its height is deliberate: the LiDAR plane passes over low obstacles, and this sensor does not.

**Costmap integration.** The `nav2_costmap_2d::RangeSensorLayer` plugin consumes `/front_range` in both the local and the global costmap. Adding it to the global costmap matters, because otherwise the planner keeps proposing paths through the box and only the local controller knows about it.

**Transform.** The range link is part of the Gazebo model but not of the URDF that `robot_state_publisher` uses, so a static transform from `base_link` to `front_range_link` is published separately.

## Repository layout

```
.
├── config/
│   └── range_layer.yaml            Costmap layer settings (reference copy)
├── docs/
│   ├── setup.md                    Step-by-step reproduction guide
│   ├── troubleshooting.md          Problems hit during development and their fixes
│   └── images/                     Screenshots used in this README
├── launch/
│   └── range_sensor_tf.launch.py   Static transform for the range sensor
├── models/
│   ├── front_range_sensor.sdf.xml  Range sensor block (reference copy)
│   └── low_box.sdf                 8 cm test obstacle
└── scripts/
    ├── configure_camera.py         Reduce camera resolution and rate in model.sdf
    ├── add_range_sensor.py         Insert the range sensor into model.sdf
    ├── add_range_layer.py          Add the range layer to a Nav2 params file
    ├── map_to_gazebo.py            Convert map coordinates to Gazebo coordinates
    ├── grab_frame.py               Save one camera frame and print pixel statistics
    └── clean_gz.sh                 Kill stale Gazebo/ROS processes before launching
```

The scripts patch the TurtleBot3 model and the stock Nav2 parameters in place, instead of shipping modified copies. That keeps the repository small and makes every change visible and repeatable.

## Requirements

- Ubuntu 22.04 (tested under WSL2)
- ROS 2 Humble
- Gazebo Classic 11 with `gazebo_ros_pkgs`
- TurtleBot3 packages, with `TURTLEBOT3_MODEL=waffle`, built from source in `~/turtlebot3_ws` so the model file can be edited
- Nav2 (`navigation2`, `nav2_bringup`) and `turtlebot3_navigation2`
- `ros-humble-rmw-cyclonedds-cpp`
- A saved map and a Gazebo world to navigate in

## Quick start

The full walkthrough, including checks after each step, is in [docs/setup.md](docs/setup.md). In short:

```bash
# 1. Use CycloneDDS (needed for the camera images to reach ROS under WSL2)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# 2. Patch the robot model
python3 scripts/configure_camera.py
python3 scripts/add_range_sensor.py
cd ~/turtlebot3_ws && colcon build --packages-select turtlebot3_gazebo && source install/setup.bash

# 3. Create Nav2 parameters that include the range layer
mkdir -p ~/nav2_params
cp /opt/ros/humble/share/turtlebot3_navigation2/param/humble/waffle.yaml ~/nav2_params/waffle.yaml
python3 scripts/add_range_layer.py ~/nav2_params/waffle.yaml ~/nav2_params/waffle_range.yaml

# 4. Launch (one terminal each)
ros2 launch turtlebot3_gazebo <your_world>.launch.py
ros2 launch launch/range_sensor_tf.launch.py
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True \
  map:=<path/to/map.yaml> params_file:=$HOME/nav2_params/waffle_range.yaml
```

Then spawn `models/low_box.sdf` in front of the robot, set the initial pose in RViz, and send a goal beyond the box.

## Design notes

**Why a separate low sensor?** The point of the experiment is to show a gap in LiDAR-only navigation and a cheap way to close it. A low, narrow range sensor is a reasonable stand-in for a bumper-height ultrasonic or time-of-flight sensor on a real robot.

**Why the range layer in both costmaps?** The local costmap drives the controller, and the global costmap drives the planner. With the layer only in the local costmap the robot can see the box but still tends to follow a global path through it.

**Why CycloneDDS?** With the default Fast DDS the small LiDAR messages arrived normally, but the roughly 0.9 MB camera images did not. Switching the middleware fixed this. See the troubleshooting guide for how the problem was narrowed down.

## Known limitations

- The sensor is simulated, so the readings are noise-free. A real sensor would need tuning of the layer's thresholds.
- The range cone is narrow (0.4 rad). Obstacles that are off-axis and low may not be seen until the robot turns toward them.
- Tested in one world with one obstacle layout.
- The camera feed is published but not yet processed. Object detection on this feed is the next step.

## Next steps

- Colour-based object detection on `/camera/image_raw`, using the published camera intrinsics.
- Using detections for navigation goals.
- Repeating the obstacle test in Isaac Sim.

## Author

Shreyas R, B.E. Electronics and Instrumentation Engineering, M.S. Ramaiah Institute of Technology. GitHub: [shreyas02005-sudo](https://github.com/shreyas02005-sudo)

## License

Released under the [MIT License](LICENSE).
