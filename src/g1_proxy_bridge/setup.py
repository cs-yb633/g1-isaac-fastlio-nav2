from setuptools import setup

package_name = 'g1_proxy_bridge'

setup(
    name=package_name,
    version='0.2.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['../../launch/g1_proxy_bridge.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cs-yb633',
    maintainer_email='replace-with-your-email@example.com',
    description='Expose Isaac Sim Carter topics as Unitree G1-style /g1/* ROS 2 interfaces.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'g1_proxy_bridge_node = g1_proxy_bridge.g1_proxy_bridge_node:main',
            'g1_topic_monitor = g1_proxy_bridge.g1_topic_monitor:main',
        ],
    },
)
