from glob import glob

from setuptools import find_packages, setup

package_name = "robotics_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/config/shared", glob("config/shared/*.yaml")),
        (f"share/{package_name}/config/per_device/nexus", glob("config/per_device/nexus/*.yaml")),
        (f"share/{package_name}/config/per_robot/atlas", glob("config/per_robot/atlas/*.yaml")),
        (f"share/{package_name}/config/per_robot/vector", glob("config/per_robot/vector/*.yaml")),
        (f"share/{package_name}/security/policies", glob("security/policies/*.xml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="zyx",
    maintainer_email="zyx@example.invalid",
    description="Role-specific launch, layered parameters, and security profiles for the robotics harness.",
    license="Apache-2.0",
    tests_require=["pytest"],
)
