# Setup and reproduction guide

This guide reproduces the camera and range sensor test from a working TurtleBot3 + Nav2 setup. Run each long-lived command in its own terminal. Every terminal that talks to the simulation needs `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` (put it in `~/.bashrc`).

## 1. Patch the robot model

```bash
python3 scripts/configure_camera.py
python3 scripts/add_range_sensor.py
```

Both scripts default to `~/turtlebot3_ws/src/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf`. Pass a different path as the first argument if yours lives elsewhere. Each script writes a `.bak` backup next to the file and is safe to run twice.

Rebuild, then check that the installed copy picked up the change, because Gazebo loads the model from `install/`:

```bash
cd ~/turtlebot3_ws
colcon build --packages-select turtlebot3_gazebo
source install/setup.bash
grep -c front_range install/turtlebot3_gazebo/share/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf
```

The count should be above zero. If it is zero, copy `src/.../model.sdf` over the installed one by hand.

## 2. Check the sensors

Start Gazebo with your world, then:

```bash
ros2 topic echo /front_range --once
python3 scripts/grab_frame.py /tmp/frame.png
```

The range message should show a `range` value between `min_range` and `max_range`. The frame script prints `min`, `max` and `mean` pixel values; a mean near zero means a black image. Drive towards a wall with `teleop_keyboard` and confirm the range value falls.

Note: `rqt_image_view` and `ros2 topic hz` can misbehave with this camera under WSL2 even when the data is fine. RViz's Image display or `grab_frame.py` are more reliable checks. See the troubleshooting guide.

## 3. Publish the range sensor transform

```bash
ros2 launch launch/range_sensor_tf.launch.py
```

Verify it:

```bash
ros2 run tf2_ros tf2_echo base_link front_range_link
```

Keep this running during the whole test.

## 4. Create the Nav2 parameters

```bash
mkdir -p ~/nav2_params
cp /opt/ros/humble/share/turtlebot3_navigation2/param/humble/waffle.yaml ~/nav2_params/waffle.yaml
python3 scripts/add_range_layer.py ~/nav2_params/waffle.yaml ~/nav2_params/waffle_range.yaml
```

The script reports that `range_layer` was added to both `local_costmap` and `global_costmap`. After launching Nav2 you can confirm it with:

```bash
ros2 param get /local_costmap/local_costmap plugins
ros2 param get /global_costmap/global_costmap plugins
```

## 5. Launch Nav2 and localise

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True \
  map:=<path/to/map.yaml> params_file:=$HOME/nav2_params/waffle_range.yaml
```

In RViz, set the 2D Pose Estimate at the robot's position, and check that the red LiDAR points sit on the walls of the map before going further. A wrong localisation puts the obstacle in the wrong place in the costmap and ruins the test.

## 6. Place the obstacle

The map frame and the Gazebo world frame can differ by a constant shift. Measure it once with the robot localised:

```bash
ros2 topic echo /amcl_pose --once      # map frame
gz model -m waffle -p                  # Gazebo world frame
```

`offset = gazebo - map`, for x and y. In the setup this was developed on, the offset was about (-1.02, -3.98), because the map was built starting from the robot's spawn point. Yours will differ. Then convert any point you click in RViz (`Publish Point`, then `ros2 topic echo /clicked_point`):

```bash
python3 scripts/map_to_gazebo.py MAP_X MAP_Y OFFSET_X OFFSET_Y
```

Spawn the box at the converted coordinates:

```bash
ros2 run gazebo_ros spawn_entity.py -entity low_box -file models/low_box.sdf -x GZ_X -y GZ_Y -z 0.04
```

Put the robot about 1.5 m from the box, facing it. Check in RViz that the box shows up in both `/global_costmap/costmap` and `/local_costmap/costmap`, and in the same place as in Gazebo.

## 7. Run both configurations

1. **With the range layer:** send a Nav2 goal beyond the box. The planned path should bend around it.
2. **Baseline:** stop Nav2, reset the robot to the same start pose, relaunch Nav2 without `params_file` (stock parameters) and send the same goal. The robot should drive into the box, because neither the LiDAR nor the stock costmap sees it.

Before each run, set the 2D Pose Estimate again. Use the same start pose, box position and goal in both runs, otherwise the comparison is not fair.
