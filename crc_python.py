# SPDX-License-Identifier: MIT

from typing import Union
import math


def reflect_bits(data: int, length: int):
    result = 0
    for i in range(length):
        current_bit = (data & (1 << i)) >> i
        result |= current_bit << (length - 1 - i)

    return result


def compute_crc(polynomial: int, data: Union[int, bytes], data_length: int = -1, initial: int = 0, reflect_input: bool = False,
        reflect_output: bool = False, final_xor: int = 0):
    crc_length = math.ceil(math.log2(polynomial)) - 1

    if type(data) is int:
        input_data = data
    elif type(data) is bytes:
        input_data = 0
        for b in data:
            input_data <<= 8
            input_data |= b
    else:
        raise ValueError("Invalid input data type, must be int or bytes")

    if data_length == -1:
        if type(data) is int and initial != 0:
            raise ValueError("data length must be provided if initial value is non-zero")
        else:
            if type(data) is int:
                data_length = math.ceil(math.log2(data))
            else:
                data_length = len(data) * 8

    if reflect_input and not data_length % 8 == 0:
        raise ValueError("Reflected input bytes is only supported for data lengths divisible by 8")

    if reflect_input:
        result = 0
        for i in range(int(data_length / 8)):
            mask = 0xFF << (i * 8)
            byte = (input_data & mask) >> (i * 8)
            result |= reflect_bits(byte, 8) << (i * 8)
    else:
        result = input_data

    result <<= crc_length
    result ^= initial << data_length

    shifted_poly = polynomial << data_length

    while shifted_poly >= polynomial:
        if (result ^ shifted_poly) <= result:
            result ^= shifted_poly

        shifted_poly >>= 1

    if reflect_output:
        result = reflect_bits(result, crc_length)

    return result ^ final_xor