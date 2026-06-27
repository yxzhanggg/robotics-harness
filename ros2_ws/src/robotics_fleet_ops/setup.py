from setuptools import find_packages, setup

package_name = "robotics_fleet_ops"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="zyx",
    maintainer_email="zyx@example.invalid",
    description="Fleet runtime operations tools for launch orchestration, log collection, systemd, and SROS2.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "fleet_ops = robotics_fleet_ops.fleet_ops:main",
            "rosout_collector = robotics_fleet_ops.rosout_collector:main",
        ],
    },
)
