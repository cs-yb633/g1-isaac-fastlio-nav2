from setuptools import setup

package_name = 'g1_proxy_bridge'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/g1_proxy_bridge.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your_email@example.com',
    description='Expose Isaac Sim Carter topics as Unitree G1-style /g1/* ROS 2 interfaces.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'g1_proxy_bridge_node = g1_proxy_bridge.g1_proxy_bridge_node:main',
        ],
    },
)
