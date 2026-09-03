from setuptools import find_packages, setup


package_name = "g1_nav_control"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="G1 Nav maintainers",
    maintainer_email="maintainers@example.invalid",
    description="ROS 2 control utilities for G1 navigation.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "g1_fsm_tool = g1_nav_control.g1_fsm_tool:main",
            "g1_cmd_vel_executor = g1_nav_control.g1_cmd_vel_executor:main",
        ],
    },
)
