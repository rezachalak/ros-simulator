# Project Memories — ros-simulator

## Stack
- **ROS 2 Iron** on Ubuntu 22.04 (Jammy) base images
- **Gazebo Classic 11** via `ros-iron-gazebo-ros-pkgs`
- **CycloneDDS** (`rmw_cyclonedds_cpp`) for reliable ROS 2 node discovery across Docker containers
- **noVNC + x11vnc + Xvfb** for browser-based GUI (no XQuartz needed on macOS) — access at `http://localhost:8080/vnc.html`

## Services (docker-compose.yml)
| Service              | Role                                               |
|----------------------|----------------------------------------------------|
| `obstacle_detector`  | Node 1 — reads `/scan`, publishes `/obstacle_info` |
| `robot_controller`   | Node 2 — reads `/obstacle_info`, publishes `/cmd_vel` |
| `desktop`            | Gazebo + RViz2 via noVNC                           |

## Data flow
```
Gazebo (/scan) → obstacle_detector → /obstacle_info → robot_controller → /cmd_vel → Gazebo
```

## Key files
- `ros_ws/src/obstacle_avoidance/` — Python ROS 2 package (both nodes)
- `models/simple_robot/model.sdf` — diff-drive robot with 360° lidar
- `worlds/obstacle_world.world` — 8×8 m arena with 7 static obstacles
- `rviz/config.rviz` — pre-configured with LaserScan + Odometry + TF
- `cyclonedds.xml` — DDS config binding to `eth0` with multicast enabled (`Interfaces/NetworkInterface` syntax — the older `NetworkInterfaceAddress` is deprecated)
- `scripts/start_desktop.sh` — desktop container entrypoint

## Obstacle avoidance logic (robot_controller.py)
- `STOP_DISTANCE = 0.6 m` — trigger threshold
- State: FORWARD → TURNING (chosen by side with more free space) → FORWARD
- Turn duration: 2 seconds at 0.6 rad/s

## Build & run
```bash
docker compose build
docker compose up
```
Then open http://localhost:8080/vnc.html in a browser.

## Known constraints
- Software rendering only (no GPU in container) — Gazebo uses LLVMpipe; may be slow on low-end hardware.
- All services pinned to `platform: linux/arm64` so they run native on Apple Silicon (no QEMU emulation).
- **All services use `network_mode: bridge` (default `docker0`), NOT a user-defined bridge.** User-defined bridges in Colima reject `setsockopt(IP_MULTICAST_IF)` on `eth0` ("Unsupported"); `docker0` allows it. Both CycloneDDS and Gazebo Classic 11 transport require working multicast on eth0. CycloneDDS multicast peer discovery handles cross-container DDS — service-name DNS from Compose is not needed.
  - ✅ **Colima with `--vm-type=vz` + default bridge** — works.
  - ❌ **Docker Desktop for Mac** (any bridge) — `IP_MULTICAST_IF` always returns `Unsupported`; Gazebo Classic crashes with `std::out_of_range` during transport init. CycloneDDS can be forced to unicast (`AllowMulticast: false` + `Peers`) but Gazebo cannot.
  - ❌ **Colima + user-defined bridge** — also fails (`docker0` only).
