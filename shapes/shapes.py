import rclpy
from rclpy.node import Node
from turtlesim.srv import Spawn
from geometry_msgs.msg import Twist
from time import sleep
import threading
import math

class TurtleShapeDrawer(Node):
    def __init__(self):
        super().__init__('turtle_shape_drawer')
        self.spawn_positions = [
            (8.0, 5.0),  # Kaplumbağa 1: Kare
            (2.0, 6.0),  # Kaplumbağa 2: Altıgen
            (1.0, 2.0),  # Kaplumbağa 3: Yıldız
            (7.0, 2.0),  # Kaplumbağa 4: Üçgen
            (7.0, 8.5)   # Kaplumbağa 5: Beşgen
        ]
        self.shapes = ['square', 'hexagon', 'star', 'triangle', 'pentagon']
        self.spawn_turtles()
        self._publishers = {}  # Publisher'ları burada tanımlıyoruz.

    def spawn_turtles(self):
        for i, (x, y) in enumerate(self.spawn_positions):
            self.spawn_turtle(i + 1, x, y)

    def spawn_turtle(self, index, x, y):
        client = self.create_client(Spawn, '/spawn')
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service /spawn not available, waiting again...')
        request = Spawn.Request()
        request.x = x
        request.y = y
        request.theta = 0.0
        request.name = f'turtle{index}'
        future = client.call_async(request)
        future.add_done_callback(lambda future: self.spawn_callback(future, index))

    def spawn_callback(self, future, index):
        try:
            future.result()
            self.get_logger().info(f'Turtle {index} spawned')
            self._publishers[index] = self.create_publisher(Twist, f'/turtle{index}/cmd_vel', 10)
            if len(self._publishers) == len(self.spawn_positions):
                self.start_drawing()
        except Exception as e:
            self.get_logger().error(f'Failed to spawn turtle {index}: {e}')

    def start_drawing(self):
        threads = []
        for i, shape in enumerate(self.shapes):
            t = threading.Thread(target=getattr(self, f'draw_{shape}'), args=(i + 1,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    def draw_square(self, index):
        for _ in range(4):
            self.move_straight(index, 2.0)
            self.rotate(index, math.pi / 2)

    def draw_hexagon(self, index):
        for _ in range(6):
            self.move_straight(index, 1.5)
            self.rotate(index, math.pi / 3)

    def draw_star(self, index):
        for _ in range(5):
            self.move_straight(index, 2.0)
            self.rotate(index, 4 * math.pi / 5)

    def draw_triangle(self, index):
        for _ in range(3):
            self.move_straight(index, 2.0)
            self.rotate(index, 2 * math.pi / 3)

    def draw_pentagon(self, index):
        for _ in range(5):
            self.move_straight(index, 1.5)
            self.rotate(index, 2 * math.pi / 5)

    def move_straight(self, index, distance):
        twist = Twist()
        twist.linear.x = 1.0
        duration = distance / twist.linear.x
        self.publish(twist, index, duration)

    def rotate(self, index, angle):
        twist = Twist()
        twist.angular.z = angle / 1.5
        duration = abs(angle) / abs(twist.angular.z)
        self.publish(twist, index, duration)

    def publish(self, twist, index, duration):
        publisher = self._publishers[index]
        end_time = self.get_clock().now() + rclpy.time.Duration(seconds=duration)
        while self.get_clock().now() < end_time:
            publisher.publish(twist)
            sleep(0.1)
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        publisher.publish(twist)
        sleep(1)

def main(args=None):
    rclpy.init(args=args)
    node = TurtleShapeDrawer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
