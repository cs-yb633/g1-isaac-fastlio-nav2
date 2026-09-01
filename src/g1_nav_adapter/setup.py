from setuptools import find_packages, setup


package_name = "g1_nav_adapter"

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
    description="Read-only odometry to TF adapter for G1 navigation.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "g1_odom_tf_node = g1_nav_adapter.g1_odom_tf_node:main",
            "dog_odom_probe = g1_nav_adapter.dog_odom_probe:main",
            "dog_odom_analyze = g1_nav_adapter.odom_analysis:main",
        ],
    },
)
