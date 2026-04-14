
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # 1. Driver Node (Mcnamu)
    driver_node = Node(
        package='yahboomcar_bringup',
        executable='Mcnamu_driver',
        name='driver_node',
        output='screen'
    )

    # 2. Camera Node
    camera_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        output='screen',
        parameters=[{
            'video_device': '/dev/video0',
            'image_width': 640,
            'image_height': 480,
            'pixel_format': 'yuyv',
            'camera_frame_id': 'usb_cam',
            'io_method': 'mmap',
        }]
    )

    # 3. OLED Node
    oled_node = Node(
        package='yahboomcar_apriltag',
        executable='oled_node',
        name='oled_node',
        output='screen'
    )

    return LaunchDescription([
        driver_node,
        camera_node,
        oled_node
    ])
