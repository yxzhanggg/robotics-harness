from robotics_fleet_ops.fleet_ops import main
from robotics_fleet_ops.model import DEVICES
from robotics_fleet_ops.model import expand_target
from robotics_fleet_ops.rendering import launch_command
from robotics_fleet_ops.rendering import security_create_command
from robotics_fleet_ops.rendering import service_unit
from robotics_fleet_ops.rendering import tmux_up_command


def test_expand_target_supports_groups():
    assert [device.name for device in expand_target("robots")] == ["atlas", "vector"]
    assert [device.name for device in expand_target("all")] == ["nexus", "atlas", "vector"]


def test_robot_launch_uses_watchdog_not_driver_cmd_vel():
    command = launch_command(DEVICES["atlas"])
    assert "robotics_bringup robot.launch.py robot_name:=atlas" in command
    assert "cmd_vel_safe" not in command


def test_nexus_launch_can_enable_security_and_rosout_collection():
    command = tmux_up_command(DEVICES["nexus"], security=True, collect_rosout=True)
    assert "ROS_SECURITY_ENABLE=true" in command
    assert "security_strategy:=Enforce" in command
    assert "enable_rosout_collector:=true" in command


def test_service_unit_is_user_service_for_runtime_launch():
    unit = service_unit(DEVICES["vector"], security=True)
    assert "system" not in unit.lower()
    assert "robot.launch.py robot_name:=vector" in unit
    assert "ROS_SECURITY_STRATEGY=Enforce" in unit


def test_security_create_declares_expected_enclaves():
    command = security_create_command()
    assert "/multi_robot_teleop" in command
    assert "/atlas/cmd_vel_watchdog" in command
    assert "/vector/cmd_vel_watchdog" in command


def test_cli_dry_run_does_not_execute_ssh(capsys):
    result = main(["status", "nexus", "--dry-run"])
    captured = capsys.readouterr()
    assert result == 0
    assert "ssh nexus" in captured.out
