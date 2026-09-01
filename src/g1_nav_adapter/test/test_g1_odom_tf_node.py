import rclpy
from nav_msgs.msg import Odometry

from g1_nav_adapter.g1_odom_tf_node import G1OdomTfNode


class _RecordingBroadcaster:
    def __init__(self):
        self.calls = []

    def sendTransform(self, transforms):
        self.calls.append(transforms)


def _message(index, x=0.1):
    message = Odometry()
    message.header.stamp.sec = index
    message.header.frame_id = "odom"
    message.child_frame_id = "robot_center"
    message.pose.pose.position.x = x
    message.pose.pose.position.z = 0.7
    message.pose.pose.orientation.w = 1.0
    return message


def test_node_publishes_fifth_valid_sample_with_original_stamp_only():
    rclpy.init()
    node = G1OdomTfNode()
    recorder = _RecordingBroadcaster()
    node._broadcaster = recorder
    try:
        for index in range(1, 5):
            node._on_odometry(_message(index))
            assert recorder.calls == []
        node._on_odometry(_message(5))
        assert len(recorder.calls) == 1
        assert len(recorder.calls[0]) == 2
        assert all(transform.header.stamp.sec == 5 for transform in recorder.calls[0])
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_node_resets_startup_streak_and_skips_post_qualification_bad_sample():
    rclpy.init()
    node = G1OdomTfNode()
    recorder = _RecordingBroadcaster()
    node._broadcaster = recorder
    try:
        node._on_odometry(_message(1))
        node._on_odometry(_message(2))
        node._on_odometry(_message(3, x=4.009699584e24))
        for index in range(4, 8):
            node._on_odometry(_message(index))
        assert recorder.calls == []
        node._on_odometry(_message(8))
        assert len(recorder.calls) == 1

        node._on_odometry(_message(9, x=4.009699584e24))
        assert len(recorder.calls) == 1
        assert node._qualification.statistics.qualified

        node._on_odometry(_message(10))
        assert len(recorder.calls) == 2
        assert recorder.calls[-1][0].header.stamp.sec == 10
    finally:
        node.destroy_node()
        rclpy.shutdown()
