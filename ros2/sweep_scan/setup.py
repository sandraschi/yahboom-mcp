from setuptools import setup
setup(
    name="sweep_scan",
    version="1.0.0",
    py_modules=["sweep_scan_node"],
    entry_points={"console_scripts": ["sweep_scan = sweep_scan_node:main"]},
)
