from glob import glob

from setuptools import find_packages, setup

package_name = "pi_peripheral_lab"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml", "README.md"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/docs/labs", glob("docs/labs/*.md")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="zyx",
    maintainer_email="zyx@example.invalid",
    description=(
        "Reusable Raspberry Pi electrical and peripheral engineering lab for "
        "safe ROS2 hardware experiments."
    ),
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "gpio_output_node = pi_peripheral_lab.gpio_output_node:main",
            "pwm_scope_node = pi_peripheral_lab.pwm_scope_node:main",
            "gpio_handshake_main_node = pi_peripheral_lab.gpio_handshake_main_node:main",
            "gpio_handshake_peer_node = pi_peripheral_lab.gpio_handshake_peer_node:main",
            "uart_tx_node = pi_peripheral_lab.uart_tx_node:main",
            "uart_rx_node = pi_peripheral_lab.uart_rx_node:main",
            "spi_wave_node = pi_peripheral_lab.spi_wave_node:main",
            "i2c_probe_node = pi_peripheral_lab.i2c_probe_node:main",
            "adc_reader_node = pi_peripheral_lab.adc_reader_node:main",
            "dac_output_node = pi_peripheral_lab.dac_output_node:main",
            "frequency_counter_node = pi_peripheral_lab.frequency_counter_node:main",
            "can_sender_node = pi_peripheral_lab.can_sender_node:main",
            "can_receiver_node = pi_peripheral_lab.can_receiver_node:main",
            "rs485_sender_node = pi_peripheral_lab.rs485_sender_node:main",
            "rs485_receiver_node = pi_peripheral_lab.rs485_receiver_node:main",
            "load_driver_node = pi_peripheral_lab.load_driver_node:main",
            "joy_control_mapper_node = pi_peripheral_lab.joy_control_mapper_node:main",
        ],
    },
)
