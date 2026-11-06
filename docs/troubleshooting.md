# Troubleshooting

These are the main issues I encountered while building the project, along with the checks and fixes that helped identify them.

## Camera topics exist, but no images arrive

**Symptom:** `/camera/image_raw` and `/camera/camera_info` are listed with one publisher, and `/scan` publishes normally, but `ros2 topic hz /camera/image_raw` prints nothing. Camera info arrives as expected.

**Diagnosis:** Gazebo's own camera topic was active (`gz topic -z /gazebo/default/waffle/camera_rgb_frame/camera/image` showed about 9.5 Hz), so rendering was not the issue. A 640x480 RGB frame is about 0.9 MB, much larger than a scan message. Under WSL2, large messages did not pass reliably with the default Fast DDS setup.

**Fix:** Install CycloneDDS and use it in every terminal, including the one running Gazebo:

```bash
sudo apt install ros-humble-rmw-cyclonedds-cpp
echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
```

## The stock camera uses more resources than needed

The stock Waffle camera renders at 1920x1080 and 30 Hz with a 300 m far clip. I initially reduced these settings while investigating the missing images; the middleware was the underlying issue, but the smaller settings are still useful for keeping Gazebo responsive.

**Fix:** Run `scripts/configure_camera.py` to set the camera to 640x480 at 10 Hz with a 10 m far clip. These settings are sufficient for colour-based detection.

## The model does not change after `colcon build`

**Cause:** Gazebo loads `model.sdf` from the `install/` tree. The build reported that `turtlebot3_gazebo` was already present in an underlay workspace, and the installed copy was out of date.

**Fix:** After building, check the installed file with `grep`. If needed, copy the source file over it by hand; see step 1 in the [setup guide](setup.md).

## `rqt_image_view` shows a black image, or `ros2 topic hz` prints nothing

**Cause:** Under WSLg, neither tool was a reliable way to check this camera. In Humble, `ros2 topic hz` subscribes with best-effort QoS, which did not work well with large fragmented messages. `rqt_image_view` showed a black image even while valid camera data was available.

**How I checked:** `scripts/grab_frame.py` subscribes with reliable QoS, prints pixel statistics (`min=0 max=168 mean=92.4` for a correct frame), and saves a PNG. The saved image was correct. RViz's Image display also worked after setting the topic reliability to Reliable.

## Costmap reports `Invalid frame ID "front_range_link"`

**Cause:** The range link is in the Gazebo model but not in the URDF read by `robot_state_publisher`, so its transform was not published. Without the transform, the costmap could not place sensor readings reliably. In the first test run, this appeared as the robot pausing and then hitting the box.

**Fix:** Launch `launch/range_sensor_tf.launch.py` before Nav2 and keep it running. Verify the transform with `ros2 run tf2_ros tf2_echo base_link front_range_link`.

## The obstacle appears in the wrong place, or the robot leaves the map

**Cause:** The Nav2 map frame and Gazebo world frame are offset by a constant shift. Coordinates selected in RViz are map coordinates, while `spawn_entity.py` and `gz model` use Gazebo coordinates. Using Gazebo coordinates for `/initialpose` also placed the robot outside the map.

**Fix:** Measure the offset as described in [step 6 of the setup guide](setup.md#6-place-the-low-box), then convert coordinates with `scripts/map_to_gazebo.py`. Give AMCL map coordinates and Gazebo commands Gazebo coordinates.

## The obstacle appears in the local costmap, but the robot still collides

**Cause:** The local costmap alone is not enough. If the global planner does not know about the obstacle, it can keep planning through it.

**Fix:** Add `range_layer` to both costmaps. `scripts/add_range_layer.py` does this.

## Gazebo launches once, then fails on the next attempt

**Cause:** `gzserver` or `gzclient` processes from the previous session may still be running.

**Fix:** Run `scripts/clean_gz.sh` before launching again. A message such as `[spawn_entity.py-4] process has finished cleanly` immediately after the robot spawns is normal; that helper exits after placing the robot in the world.
