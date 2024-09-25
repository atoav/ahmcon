# ahmcon

Python3 bindings to the AHM TCP/IP Protocol Firmware V1.4 as used in the Allen & Heath AHM-series. Requires no external dependencies as it runs with raw sockets.

Not all things are implemented, only those I needed, that means, setting/getting levels, muting. Implementing the rest should be trivial if you have some python experience.

Feel free to take the code from `src/ahmcon/ahm.py` and build on it. There is a `example()` function that you can check out.

> [!NOTE]  
> I wrote this code so you don't have to. That – however – does not mean I am willing to invest a lot of time into answering support questions of why something isn't working for your specific installation. PRs that improve the capabilities/coverage/performance or help keeping up with new API versions are welcome tho.

## Example

```python
# Create a Object for the ahm using its IP and firmware version
ahm = Ahm16("192.168.1.25", version="1.43")

# Recall Preset 1
ahm.preset_recall(1)
print("Recalled preset 1\n")

# Get some input levels
level_for_input_1 = ahm.get_input_level(1)
level_for_input_2 = ahm.get_input_level(2)
print(f"The level for input 1 is {level_for_input_1} dB")
print(f"The level for input 2 is {level_for_input_2} dB")

# Set some levels
level = 0.0
print("\nSetting all Input-Faders:")
for i in range(1, 17):
    print(f"    Set level for input {i} to {level} dB")
    ahm.set_input_level(i, level)

# Check which inputs are muted
print("\nCheck if inputs are muted or active:")
for i in range(1, 17):
    muted = ahm.get_input_muted(i)
    print(f"   Input {i}: {'muted' if muted else 'active'}")
```
