# Setup and reproduction guide

This guide covers adding the camera and range sensor to a working TurtleBot3 Waffle and Nav2 setup, then reproducing the obstacle demonstration. Run each long-lived command in its own terminal. Set `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` in every terminal that communicates with the simulation (for example, add it to `~/.bashrc`).

## 1. Update the robot model

```bash
python3 scripts/configure_camera.py
python3 scripts/add_range_sensor.py
```

By default, both scripts target `~/turtlebot3_ws/src/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf`. Pass a different model path as the first argument if needed. The scripts create a `.bak` or `.bak2` backup beside the model file. They leave the file unchanged when the requested camera settings or range sensor are already present.

Rebuild the package, then check that the installed model includes the changes. Gazebo loads the model from `install/`:

```bash
cd ~/turtlebot3_ws
colcon build --packages-select turtlebot3_gazebo
source install/setup.bash
grep -c front_range install/turtlebot3_gazebo/share/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf
```

The count should be above zero. If it is zero, copy `src/.../model.sdf` over the installed copy by hand.

## 2. Check the sensors

Start Gazebo with your world, then check the range topic and capture a camera frame:

```bash
ros2 topic echo /front_range --once
python3 scripts/grab_frame.py /tmp/frame.png
```

The range message should show a `range` value between `min_range` and `max_range`. The frame script prints `min`, `max`, and `mean` pixel values; a mean near zero indicates a black image. Drive toward a wall with `teleop_keyboard` and confirm that the range value falls.

Under WSL2, `rqt_image_view` and `ros2 topic hz` may misbehave with this camera even when the data is valid. RViz's Image display or `grab_frame.py` are more reliable checks. See the [troubleshooting guide](troubleshooting.md).

## 3. Publish the range sensor transform

```bash
ros2 launch launch/range_sensor_tf.launch.py
```

Verify the transform:

```bash
ros2 run tf2_ros tf2_echo base_link front_range_link
```

Keep this running throughout the test.

## 4. Create Nav2 parameters

```bash
mkdir -p ~/nav2_params
cp /opt/ros/humble/share/turtlebot3_navigation2/param/humble/waffle.yaml ~/nav2_params/waffle.yaml
python3 scripts/add_range_layer.py ~/nav2_params/waffle.yaml ~/nav2_params/waffle_range.yaml
```

The script reports that `range_layer` was added to both `local_costmap` and `global_costmap`. After launching Nav2, verify the plugin lists:

```bash
ros2 param get /local_costmap/local_costmap plugins
ros2 param get /global_costmap/global_costmap plugins
```

## 5. Launch Nav2 and localise

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True \
  map:=<path/to/map.yaml> params_file:=$HOME/nav2_params/waffle_range.yaml
```

In RViz, set the 2D Pose Estimate at the robot's position. Before continuing, check that the red LiDAR points align with the walls on the map. Incorrect localisation will place the obstacle incorrectly in the costmap and invalidate the test.

## 6. Place the obstacle

The map frame and Gazebo world frame may differ by a constant shift. Measure the offset once while the robot is localised:

```bash
ros2 topic echo /amcl_pose --once      # map frame
gz model -m waffle -p                  # Gazebo world frame
```

Calculate `offset = gazebo - map` for x and y. In the setup used during development, the offset was about (-1.02, -3.98), because the map was built starting from the robot's spawn point. Your offset will differ. To convert coordinates selected in RViz (`Publish Point`, then `ros2 topic echo /clicked_point`), run:

```bash
python3 scripts/map_to_gazebo.py MAP_X MAP_Y OFFSET_X OFFSET_Y
```

Spawn the box at the converted coordinates:

```bash
ros2 run gazebo_ros spawn_entity.py -entity low_box -file models/low_box.sdf -x GZ_X -y GZ_Y -z 0.04
```

Place the robot about 1.5 m from the box, facing it. In RViz, confirm that the box appears in both `/global_costmap/costmap` and `/local_costmap/costmap`, in the same position as in Gazebo.

## 7. Compare the two configurations

1. **With the range layer:** Send a Nav2 goal beyond the box. The planned path should bend around it.
2. **LiDAR-only baseline:** Stop Nav2, reset the robot to the intended start pose, relaunch Nav2 without `params_file` (stock parameters), and send the same goal. The robot is expected to drive into the box because neither the LiDAR nor the stock costmap detects it.

For a fair comparison, use the same start pose, box position, and goal in both runs. Re-localise with the 2D Pose Estimate before each run. These instructions describe a repeatable procedure; the recorded results are qualitative and do not establish that the original runs used identical positions.
