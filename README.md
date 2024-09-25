# ahmcon

Python3 bindings to the AHM TCP/IP Protocol Firmware V1.4 as used in the Allen & Heath AHM-series. Requires no external dependencies as it runs with raw sockets.

Not all things are implemented, only those I needed, that means, setting/getting levels, muting. Implementing the rest should be trivial if you have some python experience.

Feel free to take the code from `src/ahmcon/ahm.py` and build on it. There is a `example()` function that you can check out.
