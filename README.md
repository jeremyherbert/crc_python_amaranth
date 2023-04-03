# crc_python_amaranth

This repository contains an implementation of the CRC algorithm written in python and the [Amaranth](https://github.com/amaranth-lang/amaranth) HDL. Arbitrary polynomials as well as arbitrary input and output sizes can be used. The Amaranth core is synchronous and calculates the CRC across the entire input in one clock cycle (though it wouldn't be difficult to modify it to be completely asynchronous). 

Note that in the pure python case, the polynomial is used to detect the output size so the uppermost bit of the CRC polynomial must be set. In the Amaranth core the output size is set explicitly so the uppermost bit should not be set.

A catalog of CRC parameters can be found here: [https://reveng.sourceforge.io/crc-catalogue/](https://reveng.sourceforge.io/crc-catalogue/).

To run the tests, use `pytest test.py`.

License is MIT.