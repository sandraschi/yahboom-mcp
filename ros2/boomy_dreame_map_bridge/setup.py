import os
from glob import glob

from setuptools import find_packages, setup

package_name = "boomy_dreame_map_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Yahboom MCP",
    maintainer_email="dev@local",
    description="Dreame mcp map → Nav2 OccupancyGrid for Boomy (Raspbot v2).",
    license="MIT",
    entry_points={
        "console_scripts": [
            "dreame_map_publisher = boomy_dreame_map_bridge.dreame_map_publisher_node:main",
        ],
    },
)
