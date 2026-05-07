"""Launch the Dreame → Nav2 static floor plan publisher.

Set ``dreame_map_url`` to a reachable host running dreame-mcp (e.g. Goliath PC, not
localhost if the node runs on the Pi — use the PC LAN IP on port 10894).
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="boomy_dreame_map_bridge",
                executable="dreame_map_publisher",
                name="dreame_map_publisher",
                output="screen",
                parameters=[
                    {
                        "dreame_map_url": "http://127.0.0.1:10894/api/v1/map",
                        "http_timeout_sec": 40.0,
                        "update_period_sec": 0.0,
                        "map_frame": "map",
                        "map_topic": "/dreame_floorplan",
                        "map_resolution": 0.05,
                        "map_origin_x": 0.0,
                        "map_origin_y": 0.0,
                        "map_origin_z": 0.0,
                        "map_origin_yaw_deg": 0.0,
                        "image_free_pixel_gte": 200,
                        "image_occupied_pixel_lte": 50,
                        "flip_image_y": True,
                        "publish_map_to_odom_tf": False,
                        "odom_frame": "odom",
                    }
                ],
            ),
        ]
    )
