from pathlib import Path
import xml.etree.ElementTree as ET


PACKAGE_ROOT = Path(__file__).parents[1]


def test_launch_files_are_present():
    launch_dir = PACKAGE_ROOT / "launch"
    assert (launch_dir / "nexus.launch.py").is_file()
    assert (launch_dir / "robot.launch.py").is_file()


def test_robot_launch_keeps_drivers_on_safe_output_only():
    robot_launch = (PACKAGE_ROOT / "launch" / "robot.launch.py").read_text(encoding="utf-8")
    assert 'package="cmd_vel_watchdog"' in robot_launch
    assert "cmd_vel_safe" not in robot_launch


def test_watchdog_parameter_layers_keep_safe_topic_suffix():
    shared = (PACKAGE_ROOT / "config" / "shared" / "cmd_vel_watchdog.yaml").read_text(
        encoding="utf-8"
    )
    assert "input_topic: cmd_vel" in shared
    assert "output_topic: cmd_vel_safe" in shared


def test_security_policy_xml_is_well_formed():
    for policy in (PACKAGE_ROOT / "security" / "policies").glob("*.xml"):
        ET.parse(policy)
