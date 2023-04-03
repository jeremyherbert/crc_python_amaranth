# SPDX-License-Identifier: MIT

from amaranth import *
from amaranth.sim import Simulator


class CRC(Elaboratable):
    def __init__(self,
                 polynomial: int,
                 input_width: int,
                 output_width: int,
                 initial_value: int,
                 xor_output: int,
                 reflect_input: bool,
                 reflect_output: bool):

        self._polynomial = polynomial
        self._input_width = input_width
        self._output_width = output_width
        self._initial_value = initial_value
        self._xor_output = xor_output
        self._reflect_input = reflect_input
        self._reflect_output = reflect_output

        self.input = Signal(input_width)
        self.input_valid = Signal()
        self.output = Signal(output_width)
        self.rst = ResetSignal()
        self.clk = ClockSignal()

    def elaborate(self, platform):
        m = Module()

        stages = [Signal(self._output_width) for _ in range(self._input_width-1)]
        stages.append(Signal(self._output_width, reset=self._initial_value))  # set the reset value of the CRC register

        reflected_input = Signal(self._input_width)
        reflected_output = Signal(self._output_width)
        inverted_output = Signal(self._output_width)

        # note that this if/else is deliberately backwards! It makes the later code neater
        if self._reflect_input:
            m.d.comb += reflected_input.eq(self.input)
        else:
            m.d.comb += reflected_input.eq(self.input[::-1])

        # update CRC register
        with m.If(~self.rst & self.input_valid):
            for i in range(0, self._input_width):
                input_bit = Signal()
                shifted_out = Signal()
                input_bit_xor_shifted_out = Signal()

                m.d.comb += [
                    input_bit.eq(reflected_input[i]),
                    shifted_out.eq(stages[i-1][-1]),
                    input_bit_xor_shifted_out.eq(input_bit ^ shifted_out)
                ]

                # only the last stage should be synchronous
                if i == self._input_width - 1:
                    domain = m.d.sync
                else:
                    domain = m.d.comb

                for j in reversed(range(1, self._output_width)):
                    source_bit = stages[i-1][j-1]

                    if self._polynomial & (1 << j):
                        domain += stages[i][j].eq(source_bit ^ input_bit_xor_shifted_out)
                    else:
                        domain += stages[i][j].eq(source_bit)

                domain += stages[i][0].eq(input_bit_xor_shifted_out)

        # reflect and XOR output as necessary
        if self._reflect_output:
            m.d.comb += reflected_output.eq(stages[-1][::-1])
        else:
            m.d.comb += reflected_output.eq(stages[-1])

        if self._xor_output:
            m.d.comb += inverted_output.eq(reflected_output ^ self._xor_output)
        else:
            m.d.comb += inverted_output.eq(reflected_output)

        # connect output
        m.d.comb += self.output.eq(inverted_output)

        return m


class CRC32(CRC):
    def __init__(self, input_width):
        super().__init__(polynomial=0x04C11DB7,
                         input_width=input_width,
                         output_width=32,
                         initial_value=0xFFFFFFFF,
                         xor_output=0xFFFFFFFF,
                         reflect_input=True,
                         reflect_output=True)


def _simple_testbench():
    crc = CRC(polynomial=0x04C11DB7,
              input_width=8,
              output_width=32,
              initial_value=0xFFFFFFFF,
              xor_output=0xFFFFFFFF,
              reflect_input=True,
              reflect_output=True)

    test_crc = 0x4F5344CD

    test_data = b"\x31\x32"

    def testbench():
        yield crc.input_valid.eq(1)
        for c in test_data:
            yield crc.input.eq(c)
            yield

        yield crc.input_valid.eq(0)
        yield

        old_value = yield crc.output
        yield
        new_value = yield crc.output

        print(hex(old_value), hex(new_value))
        assert old_value == new_value
        assert test_crc == (yield crc.output)

    sim = Simulator(crc)
    sim.add_clock(10e-6)
    sim.add_sync_process(testbench)
    sim.run()


if __name__ == "__main__":
    _simple_testbench()