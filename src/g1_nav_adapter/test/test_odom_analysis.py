import pytest

from g1_nav_adapter.odom_analysis import analyze_rows


def _row(index, x, y, yaw_quaternion, valid="True"):
    return {
        "header_stamp_ns": str(1_000_000_000 + index * 20_000_000),
        "position_x": str(x),
        "position_y": str(y),
        "position_z": "0.7",
        "orientation_x": "0",
        "orientation_y": "0",
        "orientation_z": str(yaw_quaternion[0]),
        "orientation_w": str(yaw_quaternion[1]),
        "valid": valid,
    }


def test_analyzer_reports_motion_and_closure_fields():
    rows = [
        _row(0, 0.0, 0.0, (0.0, 1.0)),
        _row(1, 0.1, 0.0, (0.0, 1.0)),
        _row(2, 0.1, 0.1, (0.0, 1.0), valid="False"),
        _row(3, 0.0, 0.0, (0.0, 1.0)),
    ]
    result = analyze_rows(rows, large_jump_m=0.15)
    assert result["duration_sec"] == pytest.approx(0.06)
    assert result["mean_rate_hz"] == pytest.approx(50.0)
    # The invalid middle sample is counted but excluded from pose/path metrics.
    assert result["path_length_m"] == pytest.approx(0.2)
    assert result["net_displacement_m"] == 0.0
    assert result["closure_error_m"] == 0.0
    assert result["yaw_closure_error_rad"] == 0.0
    assert result["invalid_samples"] == 1
    assert result["rejected_samples"] == 1


def test_invalid_huge_first_sample_is_counted_but_excluded_from_pose_delta():
    rows = [
        _row(0, 4.009699584e24, 0.0, (0.0, 1.0), valid="False"),
        _row(1, 0.0, 0.0, (0.0, 1.0)),
        _row(2, 0.1, 0.0, (0.0, 1.0)),
    ]
    result = analyze_rows(rows)
    assert result["invalid_samples"] == 1
    assert result["initial_pose"]["x"] == 0.0
    assert result["delta"]["x"] == 0.1
    assert result["path_length_m"] == 0.1
    assert result["large_jumps"] == 1
