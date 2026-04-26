"""
Node 1 — obstacle_detector
===========================
Subscribes to  /scan  (LaserScan from Gazebo).
Publishes to   /obstacle_info  (geometry_msgs/Vector3):
    x = minimum distance in the FRONT sector  (-30° … +30°)
    y = minimum distance in the LEFT  sector  (30° … 90°)
    z = minimum distance in the RIGHT sector  (-90° … -30°)

A value of 999.0 means "no obstacle detected within sensor range".
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Vector3


FRONT_HALF_ANGLE = math.radians(30)   # ±30° = 60° cone ahead
SIDE_INNER       = math.radians(30)
SIDE_OUTER       = math.radians(90)
NO_OBSTACLE      = 999.0


class ObstacleDetector(Node):
    def __init__(self):
        super().__init__('obstacle_detector')

        self._pub = self.create_publisher(Vector3, '/obstacle_info', 10)
        self._sub = self.create_subscription(
            LaserScan, '/scan', self._scan_callback, 10
        )
        self.get_logger().info('obstacle_detector started — listening on /scan')

    def _scan_callback(self, msg: LaserScan) -> None:
        front_min = NO_OBSTACLE
        left_min  = NO_OBSTACLE
        right_min = NO_OBSTACLE

        for i, dist in enumerate(msg.ranges):
            if not math.isfinite(dist) or dist < msg.range_min or dist > msg.range_max:
                continue

            angle = msg.angle_min + i * msg.angle_increment

            # Normalise angle to [-π, π]
            while angle >  math.pi: angle -= 2 * math.pi
            while angle < -math.pi: angle += 2 * math.pi

            abs_angle = abs(angle)

            if abs_angle <= FRONT_HALF_ANGLE:
                front_min = min(front_min, dist)
            elif angle > SIDE_INNER and angle <= SIDE_OUTER:
                left_min = min(left_min, dist)
            elif angle < -SIDE_INNER and angle >= -SIDE_OUTER:
                right_min = min(right_min, dist)

        info = Vector3(x=front_min, y=left_min, z=right_min)
        self._pub.publish(info)

        self.get_logger().debug(
            f'front={front_min:.2f}m  left={left_min:.2f}m  right={right_min:.2f}m'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
