# Troubleshooting

Problems hit while building this, with the cause and the fix. They are listed roughly in the order they appeared.

## Camera topics exist but no images arrive

**Symptom.** `/camera/image_raw` and `/camera/camera_info` are listed, the publisher count is 1, and `/scan` publishes normally, but `ros2 topic hz /camera/image_raw` prints nothing. `camera_info` is received fine.

**Diagnosis.** Gazebo's own topic was healthy (`gz topic -z /gazebo/default/waffle/camera_rgb_frame/camera/image` showed about 9.5 Hz), so rendering was not the problem. The difference between `/scan` and the image is message size: a 640x480 RGB frame is about 0.9 MB. With the default Fast DDS under WSL2, large messages did not make it through reliably.

**Fix.** Switch the middleware in every terminal, including the one running Gazebo:

```bash
sudo apt install ros-humble-rmw-cyclonedds-cpp
echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
```

## The stock camera is heavier than it needs to be

**Context.** The stock Waffle camera renders 1920x1080 at 30 Hz with a 300 m far clip. It was reduced early on as a first suspect for the missing images. In hindsight the middleware was the real cause (see above), but the smaller size is still worth keeping.

**Fix.** `scripts/configure_camera.py` lowers it to 640x480 at 10 Hz with a 10 m far clip. That is plenty for colour-based detection and keeps Gazebo responsive.

## `colcon build` finishes but the model did not change

**Cause.** Gazebo loads `model.sdf` from the `install/` tree. The build reported that `turtlebot3_gazebo` was already present in an underlay workspace and the install copy lagged behind.

**Fix.** After building, check the installed file with `grep`, and copy the source file over it if needed (see step 1 in [setup.md](setup.md)).

## `rqt_image_view` shows a black image, `ros2 topic hz` prints nothing

**Cause.** Neither tool is a reliable test of this camera under WSLg. `ros2 topic hz` in Humble subscribes with best-effort QoS, which does not suit large fragmented messages, and `rqt_image_view` displayed black even while the data was valid.

**How it was checked.** `scripts/grab_frame.py` subscribes with reliable QoS, prints pixel statistics (`min=0 max=168 mean=92.4` for a correct frame) and saves a PNG. The saved image was correct. RViz's Image display also worked once the topic's reliability was set to Reliable.

## Costmap warns `Invalid frame ID "front_range_link"`

**Cause.** The range link is in the Gazebo model but not in the URDF that `robot_state_publisher` reads, so nothing published its transform. The costmap could not place sensor readings in the map, and the obstacle was marked unreliably. In the first test run this showed up as the robot pausing and then hitting the box.

**Fix.** Run `launch/range_sensor_tf.launch.py` before launching Nav2 and keep it running. Verify with `ros2 run tf2_ros tf2_echo base_link front_range_link`.

## The obstacle appears in the wrong place, or the robot leaves the map

**Cause.** The Nav2 map frame and the Gazebo world frame are offset by a constant shift. Coordinates picked in RViz are map coordinates, but `spawn_entity.py` and `gz model` take Gazebo coordinates. Sending Gazebo coordinates to `/initialpose` also placed the robot outside the map.

**Fix.** Measure the offset once (see [setup.md](setup.md), step 6) and convert with `scripts/map_to_gazebo.py`. Give AMCL map coordinates, and give Gazebo commands Gazebo coordinates.

## Obstacle is in the local costmap but the robot still collides

**Cause.** The local costmap alone is not enough. The global planner does not know about the obstacle and keeps planning through it.

**Fix.** Add `range_layer` to both costmaps. `scripts/add_range_layer.py` does this.

## Gazebo launches once and fails the next time

**Cause.** Leftover `gzserver` or `gzclient` processes from the previous session.

**Fix.** Run `scripts/clean_gz.sh` before every launch. Note that a line like `[spawn_entity.py-4] process has finished cleanly` right after the robot spawns is normal. That helper is supposed to exit once the robot is in the world.
