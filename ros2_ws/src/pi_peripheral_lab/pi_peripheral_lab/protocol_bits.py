"""Protocol bit helpers that are independent of ROS and hardware."""

from collections.abc import Iterable


def byte_to_bits_lsb_first(value: int, width: int = 8) -> list[int]:
    if value < 0 or value >= (1 << width):
        raise ValueError(f"value {value} does not fit in {width} bits")
    return [(value >> bit) & 1 for bit in range(width)]


def byte_to_bits_msb_first(value: int, width: int = 8) -> list[int]:
    return list(reversed(byte_to_bits_lsb_first(value, width)))


def uart_8n1_frame(byte: int) -> list[int]:
    """Return UART 8N1 wire bits: start, data LSB first, stop."""

    return [0, *byte_to_bits_lsb_first(byte, 8), 1]


def uart_bit_time_sec(baud_rate: int) -> float:
    if baud_rate <= 0:
        raise ValueError("baud_rate must be positive")
    return 1.0 / baud_rate


def spi_bits(
    payload: Iterable[int],
    bits_per_word: int = 8,
    bit_order: str = "msb",
) -> list[int]:
    bits: list[int] = []
    for byte in payload:
        if bit_order == "msb":
            bits.extend(byte_to_bits_msb_first(byte, bits_per_word))
        elif bit_order == "lsb":
            bits.extend(byte_to_bits_lsb_first(byte, bits_per_word))
        else:
            raise ValueError("bit_order must be 'msb' or 'lsb'")
    return bits


def bytes_to_hex(data: Iterable[int]) -> str:
    return " ".join(f"0x{byte & 0xff:02X}" for byte in data)


def parse_hex_bytes(text: str) -> list[int]:
    result = []
    for token in text.replace(",", " ").split():
        value = int(token, 0)
        if value < 0 or value > 0xFF:
            raise ValueError(f"byte out of range: {token}")
        result.append(value)
    return result


def i2c_7bit_address_is_valid(address: int) -> bool:
    return 0x03 <= address <= 0x77


def can_identifier_is_valid(identifier: int, extended: bool = False) -> bool:
    upper = 0x1FFFFFFF if extended else 0x7FF
    return 0 <= identifier <= upper


def crc16_modbus(data: Iterable[int]) -> int:
    """Return Modbus/RTU CRC16 for RS485 experiments."""

    crc = 0xFFFF
    for byte in data:
        crc ^= byte & 0xFF
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def rs485_lab_frame(payload: bytes, address: int = 1) -> bytes:
    """Build a tiny teaching frame: address, length, payload, CRC16 LE."""

    if address < 0 or address > 0xFF:
        raise ValueError("address must fit in one byte")
    if len(payload) > 255:
        raise ValueError("payload must fit in one-byte length")
    body = bytes([address, len(payload)]) + payload
    crc = crc16_modbus(body)
    return body + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def verify_rs485_lab_frame(frame: bytes) -> tuple[int, bytes]:
    if len(frame) < 4:
        raise ValueError("frame too short")
    body = frame[:-2]
    received = frame[-2] | (frame[-1] << 8)
    actual = crc16_modbus(body)
    if received != actual:
        raise ValueError(f"CRC mismatch: received 0x{received:04X}, actual 0x{actual:04X}")
    address = body[0]
    length = body[1]
    payload = body[2:]
    if len(payload) != length:
        raise ValueError("payload length mismatch")
    return address, payload
