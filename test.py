# SPDX-License-Identifier: MIT

import os
import struct

from amaranth.sim import Simulator

from crc_amaranth import CRC, CRC32
from crc_python import compute_crc, reflect_bits


def compute_crc32(data):
    return compute_crc(
        polynomial=0x104C11DB7,
        data=data,
        initial=0xFFFFFFFF,
        final_xor=0xFFFFFFFF,
        reflect_input=True,
        reflect_output=True,
    )


def run_sim(module, test_data, expected_crc):
    sim = Simulator(module)
    sim.add_clock(10e-6)

    def _tb():
        yield module.input_valid.eq(1)
        for c in test_data:
            yield module.input.eq(c)
            yield

        yield module.input_valid.eq(0)
        yield

        result = (yield module.output)
        print("result: 0x{:X}, expected: {:X}".format(result, expected_crc))
        assert expected_crc == result

    sim.add_sync_process(_tb)
    sim.run()


def test_python_crc():
    assert reflect_bits(0xAAAA, 16) == 0x5555
    assert reflect_bits(0x31, 8) == 0x8C
    
    assert compute_crc(0xB, int('11010011101100', 2)) == 0x4
    assert compute_crc(0x89, (1 << 38)) == 0x4A
    assert compute_crc(0x89, (1 << 38) | (17 << 32)) == 0x2A

    assert compute_crc(0x11D, 0xC2) == 0x0F
    assert compute_crc(0x11021, 0x0102) == 0x1373
    assert compute_crc(0x11021, 0x31323334) == 0xD789

    assert compute_crc(polynomial=0x11021, data=0x31, data_length=8, initial=0xFFFF) == 0xC782

    # CRC32
    assert compute_crc(0x104C11DB7, 0x31, data_length=8, initial=0xFFFFFFFF, reflect_input=True, reflect_output=True,
               final_xor=0xFFFFFFFF) == 0x83DCEFB7

    assert compute_crc(0x104C11DB7, b'12', initial=0xFFFFFFFF, reflect_input=True, reflect_output=True,
               final_xor=0xFFFFFFFF) == 0x4F5344CD

    import binascii
    for i in range(100):
        data = os.urandom(28)
        assert compute_crc(0x104C11DB7, data, initial=0xFFFFFFFF, reflect_input=True, reflect_output=True,
                   final_xor=0xFFFFFFFF) == binascii.crc32(data)


def test_crc32_simple():
    test_data = b"123456789"
    reference = 0xCBF43926
    expected_crc = compute_crc32(test_data)
    assert expected_crc == reference

    crc = CRC32(input_width=8)
    run_sim(crc, test_data, expected_crc)


def test_crc32_input_wider_than_output():
    test_data = b"12345678"
    test_data_int = struct.unpack("<Q", test_data)[0]
    reference = 0x9AE0DAAF
    expected_crc = compute_crc32(test_data)
    assert expected_crc == reference

    crc = CRC32(input_width=64)
    run_sim(crc, [test_data_int], expected_crc)


def test_crc32_random():
    for i in range(5):
        length = os.urandom(1)[0]
        test_data = os.urandom(length)
        expected_crc = compute_crc32(test_data)

        crc = CRC32(input_width=8)
        run_sim(crc, test_data, expected_crc)


def test_sd_crc7():
    # note: for the actual SD checksum, you need to compute ((x << 1) | 1) where x is the CRC7 output
    test_data = [
        (0x4A, bytes([0x40, 0x00, 0x00, 0x00, 0x00])),
        (0x2A, bytes([0x51, 0x00, 0x00, 0x00, 0x00])),
        (0x33, bytes([0x11, 0x00, 0x00, 0x09, 0x00]))
    ]

    for reference, d in test_data:
        expected_crc = compute_crc(0x89, data=d)

        assert reference == expected_crc

        crc = CRC(
            polynomial=0x09,
            input_width=8,
            output_width=7,
            initial_value=0,
            xor_output=0,
            reflect_input=False,
            reflect_output=False,
        )

        run_sim(crc, d, expected_crc)
