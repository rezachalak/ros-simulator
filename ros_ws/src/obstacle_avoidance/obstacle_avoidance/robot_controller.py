"""
Node 2 — robot_controller
==========================
Subscribes to  /obstacle_info  (geometry_msgs/Vector3, published by obstacle_detector).
Publishes to   /cmd_vel         (geometry_msgs/Twist, consumed by Gazebo diff-drive plugin).

State machine
─────────────
  FORWARD  — drive straight until something is closer than STOP_DISTANCE
  TURNING  — rotate in place; direction chosen by which side has more space
             (or randomly if both sides are equally blocked)
"""

import math
import random
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Vector3


# ── Tunable constants ──────────────────────────────────────────────────────
STOP_DISTANCE   = 0.6   # metres — stop/turn when obstacle is closer than this
FORWARD_SPEED   = 0.25  # m/s
TURN_SPEED      = 0.6   # rad/s
TURN_DURATION   = 2.0   # seconds to keep turning before checking again
NO_OBSTACLE     = 999.0
CMD_HZ          = 10    # Hz — publish rate


class State:
    FORWARD = 'FORWARD'
    TURNING = 'TURNING'


class RobotController(Node):
    def __init__(self):
        super().__init__('robot_controller')

        self._pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self._sub = self.create_subscription(
            Vector3, '/obstacle_info', self._info_callback, 10
        )
        self._timer = self.create_timer(1.0 / CMD_HZ, self._control_loop)

        self._state        = State.FORWARD
        self._turn_dir     = 1.0   # +1 = left, -1 = right
        self._turn_elapsed = 0.0
        self._front_dist   = NO_OBSTACLE
        self._left_dist    = NO_OBSTACLE
        self._right_dist   = NO_OBSTACLE

        self.get_logger().info('robot_controller started — publishing to /cmd_vel')

    # ── Receive obstacle data from Node 1 ─────────────────────────────────
    def _info_callback(self, msg: Vector3) -> None:
        self._front_dist = msg.x
        self._left_dist  = msg.y
        self._right_dist = msg.z

    # ── Control loop ───────────────────────────────────────────────────────
    def _control_loop(self) -> None:
        twist = Twist()
        dt    = 1.0 / CMD_HZ

        if self._state == State.FORWARD:
            if self._front_dist < STOP_DISTANCE:
                # Choose turn direction: away from the closer side
                if self._left_dist >= self._right_dist:
                    self._turn_dir = 1.0   # turn left (more space on left)
                elif self._right_dist > self._left_dist:
                    self._turn_dir = -1.0  # turn right (more space on right)
                else:
                    self._turn_dir = random.choice([1.0, -1.0])

                self._turn_elapsed = 0.0
                self._state = State.TURNING
                direction = 'LEFT' if self._turn_dir > 0 else 'RIGHT'
                self.get_logger().info(
                    f'Obstacle at {self._front_dist:.2f} m — turning {direction}'
                )
            else:
                twist.linear.x = FORWARD_SPEED

        elif self._state == State.TURNING:
            self._turn_elapsed += dt
            twist.angular.z = self._turn_dir * TURN_SPEED

            if self._turn_elapsed >= TURN_DURATION:
                self._state = State.FORWARD
                self.get_logger().info('Turn complete — resuming forward motion')

        self._pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
