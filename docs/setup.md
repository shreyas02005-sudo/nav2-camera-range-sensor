# Setup and reproduction guide

Follow the steps in order to add the camera and range sensor, start the simulation, and run the obstacle demonstration. This guide assumes you already have a working TurtleBot3 Waffle, ROS 2 Humble, Gazebo Classic, Nav2, a saved map, and a Gazebo world. The robot model must be editable in `~/turtlebot3_ws`.

The commands below assume you run them from the root of this repository unless a step says otherwise. Use a separate terminal for each process that must stay running. In every terminal that communicates with ROS or Gazebo, source ROS and select CycloneDDS:

```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export TURTLEBOT3_MODEL=waffle
```

In terminals that need this repository's launch files or scripts, also change to the repository directory:

```bash
cd <path/to/nav2-camera-range-sensor>
```

Replace `<path/to/nav2-camera-range-sensor>` with the directory where you cloned this repository. If you prefer, add the ROS and CycloneDDS exports to `~/.bashrc` so they are set in new terminals.

## 1. Patch and build the robot model

In a terminal at the repository root, run:

```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export TURTLEBOT3_MODEL=waffle
python3 scripts/configure_camera.py
python3 scripts/add_range_sensor.py
cd ~/turtlebot3_ws
colcon build --packages-select turtlebot3_gazebo
source install/setup.bash
```

The scripts default to `~/turtlebot3_ws/src/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf`. To use another model file, pass its path as the first argument to each script. They create backups beside the model file (`.bak` and `.bak2`).

Confirm that the installed model contains the range sensor. Gazebo loads the installed model, not just the source file:

```bash
grep -c front_range install/turtlebot3_gazebo/share/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf
```

The result should be greater than zero. If it is zero, the installed copy did not update; copy the edited source `model.sdf` over the installed one before continuing.

## 2. Start Gazebo

Open a new terminal, source ROS and set the environment variables as shown above, source the TurtleBot3 workspace overlay, then launch your world:

```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export TURTLEBOT3_MODEL=waffle
source ~/turtlebot3_ws/install/setup.bash
ros2 launch turtlebot3_gazebo <your_world>.launch.py
```

Replace `<your_world>` with the launch file for your world. Leave Gazebo running. If the robot does not appear, resolve that before continuing.

## 3. Start the range sensor transform

Open another terminal, source ROS and set the environment variables, then run this from the repository root:

```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export TURTLEBOT3_MODEL=waffle
source ~/turtlebot3_ws/install/setup.bash
cd <path/to/nav2-camera-range-sensor>
ros2 launch launch/range_sensor_tf.launch.py
```

Leave this terminal running while Nav2 is active. To check the transform, open one more sourced terminal and run:

```bash
ros2 run tf2_ros tf2_echo base_link front_range_link
```

The transform should continue publishing without frame errors.

## 4. Create Nav2 parameters with the range layer

Open a terminal, source ROS, set the environment variables from the start of this guide, and change to the repository root. Then copy the stock Waffle parameters and add the range layer:

```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export TURTLEBOT3_MODEL=waffle
cd <path/to/nav2-camera-range-sensor>
mkdir -p ~/nav2_params
cp /opt/ros/humble/share/turtlebot3_navigation2/param/humble/waffle.yaml ~/nav2_params/waffle.yaml
python3 scripts/add_range_layer.py ~/nav2_params/waffle.yaml ~/nav2_params/waffle_range.yaml
```

The script should report that `range_layer` was added to both `local_costmap` and `global_costmap`. The output file used in the next step is `~/nav2_params/waffle_range.yaml`.

## 5. Start Nav2 and set the robot pose

Open another terminal, source ROS and set the environment variables, then source the TurtleBot3 workspace overlay and launch Nav2 with your map and the new parameter file:

```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export TURTLEBOT3_MODEL=waffle
source ~/turtlebot3_ws/install/setup.bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True \
  map:=<path/to/map.yaml> params_file:=$HOME/nav2_params/waffle_range.yaml
```

Replace `<path/to/map.yaml>` with the full path to your saved map. Wait for Nav2 and RViz to finish starting. In RViz, use **2D Pose Estimate** to set the robot's position. The red LiDAR points should line up with the walls on the map before you continue; incorrect localisation shifts the obstacle in the costmap.

Check that Nav2 loaded the range plugin in both costmaps:

```bash
ros2 param get /local_costmap/local_costmap plugins
ros2 param get /global_costmap/global_costmap plugins
```

Both plugin lists should include `range_layer`.

## 6. Place the low box

First measure the offset between the map and Gazebo world frames while the robot is localised. In a sourced terminal, run:

```bash
ros2 topic echo /amcl_pose --once
gz model -m waffle -p
```

Calculate `offset = gazebo - map` separately for x and y. The offset in the development setup was about `(-1.02, -3.98)`, because the map was built from the robot's spawn point; your offset will differ.

In RViz, select **Publish Point** where you want the box to appear, then read the point in a sourced terminal:

```bash
ros2 topic echo /clicked_point --once
```

Use the point's x and y coordinates as `MAP_X` and `MAP_Y` in the conversion command. Substitute your measured x/y offsets for `OFFSET_X` and `OFFSET_Y`:

```bash
cd <path/to/nav2-camera-range-sensor>
python3 scripts/map_to_gazebo.py MAP_X MAP_Y OFFSET_X OFFSET_Y
```

The script prints the corresponding Gazebo coordinates. Substitute those numeric values for `GZ_X` and `GZ_Y` below:

```bash
ros2 run gazebo_ros spawn_entity.py -entity low_box -file models/low_box.sdf -x GZ_X -y GZ_Y -z 0.04
```

Position the robot about 1.5 m from the box, facing it. In RViz, check that the box appears at the same location as in Gazebo and is visible in both `/global_costmap/costmap` and `/local_costmap/costmap`.

## 7. Run the demonstration

With the range layer enabled, send a Nav2 goal beyond the box. The planned path should route around it.

To compare against stock Nav2 parameters:

1. Stop Nav2, but leave Gazebo and the range transform running.
2. Reset the robot and box to the intended test layout. If resetting the simulation changes the map/Gazebo relationship, repeat step 6.
3. Open a new terminal and repeat the ROS, environment, and workspace-overlay setup from step 5. Relaunch Nav2 with the same map but **without** `params_file`:

   ```bash
   ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True \
     map:=<path/to/map.yaml>
   ```

4. In RViz, set the robot's 2D Pose Estimate again and send a goal beyond the box. With stock parameters, the robot is expected to drive into the box because the LiDAR and stock costmaps do not detect it.

For a controlled repeat, use the same start pose, box position, and goal in both runs. The procedure above explains how to do that; the original recordings do not establish that the positions were identical. Results should therefore be treated as a qualitative demonstration, not a benchmark.

## Optional: verify the camera and range topics

With Gazebo running, open a sourced terminal and check that the range sensor publishes:

```bash
ros2 topic echo /front_range --once
```

The `range` value should be between `min_range` and `max_range`. To save a camera frame, run from the repository root:

```bash
python3 scripts/grab_frame.py /tmp/frame.png
```

The script prints minimum, maximum, and mean pixel values and saves the image. A mean near zero indicates a black frame. Under WSL2, `rqt_image_view` and `ros2 topic hz` may not reliably display or measure this camera stream; RViz's Image display or this saved frame are better checks. See the [troubleshooting guide](troubleshooting.md).

To run the colour-box detector and follower, continue with the [perception guide](../perception/README.md).
