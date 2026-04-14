
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    driver_node = Node(
        package='yahboomcar_bringup',
        executable='Mcnamu_driver',
        name='driver_node',
        output='screen'
    )

    usb_cam_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        parameters=[
            {'video_device': '/dev/video0'},
            {'image_width': 640},
            {'image_height': 480},
            {'pixel_format': 'yuyv'},
            {'camera_frame_id': 'camera_link'},
            {'io_method': 'mmap'}
        ],
        output='screen'
    )

    return LaunchDescription([
        driver_node,
        usb_cam_node
    ])
