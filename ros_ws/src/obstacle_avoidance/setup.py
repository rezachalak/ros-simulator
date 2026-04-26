from setuptools import setup

package_name = 'obstacle_avoidance'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dev',
    maintainer_email='dev@example.com',
    description='Obstacle avoidance demo — two communicating ROS 2 nodes',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'obstacle_detector = obstacle_avoidance.obstacle_detector:main',
            'robot_controller  = obstacle_avoidance.robot_controller:main',
        ],
    },
)
