#!/bin/bash
# Desktop entrypoint: virtual display → VNC → noVNC → Gazebo + RViz2
set -e

# ── Software rendering (no GPU required in container) ──────────────────────
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export MESA_GL_VERSION_OVERRIDE=3.3

# ── Virtual framebuffer ────────────────────────────────────────────────────
echo "[desktop] Starting virtual display :1 ..."
Xvfb :1 -screen 0 1920x1080x24 -ac &
export DISPLAY=:1
sleep 2

# ── Window manager ─────────────────────────────────────────────────────────
echo "[desktop] Starting Openbox window manager ..."
openbox &
sleep 1

# ── VNC server on port 5900 ────────────────────────────────────────────────
echo "[desktop] Starting VNC server on :5900 ..."
x11vnc -display :1 -nopw -forever -shared -rfbport 5900 \
       -o /tmp/x11vnc.log -bg
sleep 1

# ── noVNC web proxy on port 8080 ──────────────────────────────────────────
echo "[desktop] Starting noVNC on port 8080 ..."
websockify --web /usr/share/novnc 8080 localhost:5900 &
sleep 1

# ── ROS 2 environment ──────────────────────────────────────────────────────
source /opt/ros/iron/setup.bash
export GAZEBO_MODEL_PATH=/models:${GAZEBO_MODEL_PATH}

# ── Gazebo simulation ──────────────────────────────────────────────────────
echo "[desktop] Launching Gazebo with obstacle world ..."
ros2 launch gazebo_ros gazebo.launch.py \
     world:=/worlds/obstacle_world.world \
     verbose:=false &
echo "[desktop] Waiting for Gazebo to initialize (15 s) ..."
sleep 15

# ── Spawn robot into Gazebo ────────────────────────────────────────────────
echo "[desktop] Spawning simple_robot ..."
ros2 run gazebo_ros spawn_entity.py \
     -database simple_robot \
     -entity simple_robot \
     -x 0.0 -y 0.0 -z 0.1 &
sleep 3

# ── RViz2 ──────────────────────────────────────────────────────────────────
echo "[desktop] Launching RViz2 ..."
rviz2 -d /rviz/config.rviz &

echo ""
echo "============================================================"
echo "  ROS 2 Obstacle Avoidance — Desktop Ready"
echo ""
echo "  Browser  → http://localhost:8080/vnc.html"
echo "  VNC      → localhost:5900  (no password)"
echo ""
echo "  ROS topics:"
echo "    /scan           — Lidar from Gazebo"
echo "    /obstacle_info  — Processed by obstacle_detector node"
echo "    /cmd_vel        — Commands from robot_controller node"
echo "    /odom           — Robot odometry"
echo "============================================================"
echo ""

# Keep container alive
tail -f /dev/null
