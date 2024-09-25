import socket
from typing import Union, List, Optional
from itertools import batched


class Ahm16:
    def __init__(self, addr: str, version: str = None):
        self.addr = addr
        self.version = version
        self.timeout = 0.2  # Default Timeout of 200 milliseconds
        self.port = 51325  # TCP-Port as described in the documentation

        if self.version is None:
            raise ValueError(
                'Ahm16 requires you to set the correct version as a str (e.g. "1.43")'
            )

    @property
    def version_bytestring(self) -> str:
        major, minor = self.version.split(".")
        major = str(int(major)).zfill(2)
        minor = str(int(minor)).zfill(2)
        return major + minor

    def send_bytes(
        self, message: bytes, get_result=True, timeout=1.0
    ) -> Optional[bytes]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.addr, self.port))
            # This is a ugly hack. For some reason the AHM-16 won't do things unles you
            # s.recv afterwards. But if you do that, the recv will hang indefintly on
            # commands that don't give an answer. The solution I came up with is a very short
            # timeout.
            s.settimeout(timeout if get_result else 0.055)
            s.sendall(message)
            try:
                data = s.recv(1024)
            except TimeoutError:
                if not get_result:
                    return None
                print(f"Could not send message {format_bytes(message)}: Timed out")
                return None
        return data

    def send_sysex(self, message: Union[str, List[str]]):
        if isinstance(message, list):
            message = "".join(message)
        # If someone of A&H reads this: I find it absolutely disgusting that you require a version string here and I can only imagine to which problems that will lead for people who swap out your gear in highly integrated environments.
        # If you at least offered a way to _get_ the firmware version before..
        sysex_message = bytearray.fromhex(
            f"F000001A5012{self.version_bytestring}{message}"
        )
        data = self.send_bytes(sysex_message)
        return data

    def preset_recall(self, number: int):
        number = min(501, max(1, number))
        if number >= 1 and number <= 128:
            bank = "00"
        elif number <= 256:
            bank = "01"
        elif number <= 384:
            bank = "02"
        else:
            bank = "03"
        ss = f"{number:x}".zfill(2)
        message = list_to_bytes(["B0", "00", bank, "C0", ss])
        self.send_bytes(message, get_result=False)

    # ---------- INPUT MUTES ----------

    def get_input_muted(self, number: int) -> bool:
        n, ch = get_input_vars(number)
        message = [f"0{n}", "01", "09", ch, "F7"]
        result = self.send_sysex(message)
        return result[2] > 63

    def mute_input(self, number: int):
        n, ch = get_input_vars(number)
        message = list_to_bytes([f"9{n}", ch, "7F", f"9{n}", ch, "00"])
        self.send_bytes(message, get_result=False)

    def unmute_input(self, number: int):
        n, ch = get_input_vars(number)
        message = list_to_bytes([f"9{n}", ch, "3F", f"9{n}", ch, "00"])
        self.send_bytes(message, get_result=False)

    # ---------- ZONE MUTES ----------
    def get_zone_muted(self, number: int) -> bool:
        n, ch = get_zone_vars(number)
        message = [f"0{n}", "01", "09", ch, "F7"]
        result = self.send_sysex(message)
        return result[2] > 63

    def mute_zone(self, number: int):
        n, ch = get_zone_vars(number)
        message = list_to_bytes([f"9{n}", ch, "7F", f"9{n}", ch, "00"])
        self.send_bytes(message, get_result=False)

    def unmute_zone(self, number: int):
        n, ch = get_zone_vars(number)
        message = list_to_bytes([f"9{n}", ch, "3F", f"9{n}", ch, "00"])
        self.send_bytes(message, get_result=False)

    # ---------- CONTROL GROUP MUTES ----------
    def get_control_group_muted(self, number: int) -> bool:
        n, ch = get_control_group_vars(number)
        message = [f"0{n}", "01", "09", ch, "F7"]
        result = self.send_sysex(message)
        return result[2] > 63

    def mute_control_group(self, number: int):
        n, ch = get_control_group_vars(number)
        message = list_to_bytes([f"9{n}", ch, "7F", f"9{n}", ch, "00"])
        self.send_bytes(message, get_result=False)

    def unmute_control_group(self, number: int):
        n, ch = get_control_group_vars(number)
        message = list_to_bytes([f"9{n}", ch, "3F", f"9{n}", ch, "00"])
        self.send_bytes(message, get_result=False)

    # ---------- ROOM MUTES ----------
    def get_room_muted(self, number: int) -> bool:
        n, ch = get_room_vars(number)
        message = [f"0{n}", "01", "09", ch, "F7"]
        result = self.send_sysex(message)
        return result[2] > 63

    def mute_room(self, number: int):
        n, ch = get_room_vars(number)
        message = list_to_bytes([f"9{n}", ch, "7F", f"9{n}", ch, "00"])
        self.send_bytes(message, get_result=False)

    def unmute_room(self, number: int):
        n, ch = get_room_vars(number)
        message = list_to_bytes([f"9{n}", ch, "3F", f"9{n}", ch, "00"])
        self.send_bytes(message, get_result=False)

    # ---------- INPUT LEVEL ----------
    def get_input_level(self, number: int) -> int:
        n, ch = get_input_vars(number)
        message = [f"0{n}", "01", "0B", "17", ch, "F7"]
        result = self.send_sysex(message)
        # Return -inf if the result was malformed
        if result is None or len(result) != 7:
            return midi_to_db(0)
        return midi_to_db(result[6])

    def set_input_level(self, number: int, level: float):
        level = min(10.0, level)
        level_midi = db_to_midi(level)
        level_midi = f"{level_midi:x}".zfill(2)
        n, ch = get_input_vars(number)
        message = list_to_bytes(
            [
                f"B{n}",
                "63",
                ch,
                f"B{n}",
                "62",
                "17",
                ch,
                f"B{n}",
                "06",
                level_midi,
            ]
        )
        self.send_bytes(message, get_result=False)

    def increment_input_level(self, number: int):
        n, ch = get_input_vars(number)
        message = list_to_bytes(
            [f"B{n}", "63", ch, f"B{n}", "62", "20", f"B{n}", "06", "7F"]
        )
        self.send_bytes(message, get_result=False)

    def decrement_input_level(self, number: int):
        n, ch = get_input_vars(number)
        message = list_to_bytes(
            [f"B{n}", "63", ch, f"B{n}", "62", "20", f"B{n}", "06", "3F"]
        )
        self.send_bytes(message, get_result=False)

    # ---------- ZONE LEVEL ----------
    def get_zone_level(self, number: int) -> int:
        n, ch = get_zone_vars(number)
        message = [f"0{n}", "01", "0B", "17", ch, "F7"]
        result = self.send_sysex(message)
        # Return -inf if the result was malformed
        if result is None or len(result) != 7:
            return midi_to_db(0)
        return midi_to_db(result[6])

    def set_zone_level(self, number: int, level: float):
        level = min(10.0, level)
        level_midi = db_to_midi(level)
        level_midi = f"{level_midi:x}".zfill(2)
        n, ch = get_zone_vars(number)
        message = list_to_bytes(
            [
                f"B{n}",
                "63",
                ch,
                f"B{n}",
                "62",
                "17",
                ch,
                f"B{n}",
                "06",
                level_midi,
            ]
        )
        self.send_bytes(message, get_result=False)

    def increment_zone_level(self, number: int):
        n, ch = get_zone_vars(number)
        message = list_to_bytes(
            [f"B{n}", "63", ch, f"B{n}", "62", "20", f"B{n}", "06", "7F"]
        )
        self.send_bytes(message, get_result=False)

    def decrement_zone_level(self, number: int):
        n, ch = get_zone_vars(number)
        message = list_to_bytes(
            [f"B{n}", "63", ch, f"B{n}", "62", "20", f"B{n}", "06", "3F"]
        )
        self.send_bytes(message, get_result=False)

    # ---------- CONTROL GROUP LEVEL ----------
    def get_control_group_level(self, number: int) -> int:
        n, ch = get_control_group_vars(number)
        message = [f"0{n}", "01", "0B", "17", ch, "F7"]
        result = self.send_sysex(message)
        # Return -inf if the result was malformed
        if result is None or len(result) != 7:
            return midi_to_db(0)
        return midi_to_db(result[6])

    def set_control_group_level(self, number: int, level: float):
        level = min(10.0, level)
        level_midi = db_to_midi(level)
        level_midi = f"{level_midi:x}".zfill(2)
        n, ch = get_control_group_vars(number)
        message = list_to_bytes(
            [
                f"B{n}",
                "63",
                ch,
                f"B{n}",
                "62",
                "17",
                ch,
                f"B{n}",
                "06",
                level_midi,
            ]
        )
        self.send_bytes(message, get_result=False)

    def increment_control_group_level(self, number: int):
        n, ch = get_control_group_vars(number)
        message = list_to_bytes(
            [f"B{n}", "63", ch, f"B{n}", "62", "20", f"B{n}", "06", "7F"]
        )
        self.send_bytes(message, get_result=False)

    def decrement_control_group_level(self, number: int):
        n, ch = get_control_group_vars(number)
        message = list_to_bytes(
            [f"B{n}", "63", ch, f"B{n}", "62", "20", f"B{n}", "06", "3F"]
        )
        self.send_bytes(message, get_result=False)

    # ---------- ROOM LEVEL ----------
    def get_room_level(self, number: int) -> int:
        n, ch = get_room_vars(number)
        message = [f"0{n}", "01", "0B", "17", ch, "F7"]
        result = self.send_sysex(message)
        # Return -inf if the result was malformed
        if result is None or len(result) != 7:
            return midi_to_db(0)
        return midi_to_db(result[6])

    def set_room_level(self, number: int, level: float):
        level = min(10.0, level)
        level_midi = db_to_midi(level)
        level_midi = f"{level_midi:x}".zfill(2)
        n, ch = get_room_vars(number)
        message = list_to_bytes(
            [
                f"B{n}",
                "63",
                ch,
                f"B{n}",
                "62",
                "17",
                ch,
                f"B{n}",
                "06",
                level_midi,
            ]
        )
        self.send_bytes(message, get_result=False)

    def increment_room_level(self, number: int):
        n, ch = get_room_vars(number)
        message = list_to_bytes(
            [f"B{n}", "63", ch, f"B{n}", "62", "20", f"B{n}", "06", "7F"]
        )
        self.send_bytes(message, get_result=False)

    def decrement_room_level(self, number: int):
        n, ch = get_room_vars(number)
        message = list_to_bytes(
            [f"B{n}", "63", ch, f"B{n}", "62", "20", f"B{n}", "06", "3F"]
        )
        self.send_bytes(message, get_result=False)


# ================== HELPER FUNCTIONS ===================


def format_bytes(hex_bytes) -> str:
    hex_str = hex_bytes.hex().upper()
    return " ".join([a + b for a, b in batched(hex_str, 2)])


def list_to_bytes(data: List[str]) -> bytes:
    data = "".join(data)
    return bytearray.fromhex(data)


# Note: First channel is 1
def get_input_vars(number: int) -> (str, str):
    n = str(0)
    ch = min(max(0, number - 1), 15)
    ch = f"{ch:x}".zfill(2).upper()
    return (n, ch)


# Note: First channel is 1
def get_zone_vars(number: int) -> (str, str):
    n = str(1)
    ch = min(max(0, number - 1), 7)
    ch = f"{ch:x}".zfill(2).upper()
    return (n, ch)


# Note: First channel is 1
def get_control_group_vars(number: int) -> (str, str):
    n = str(2)
    ch = min(max(0, number - 1), 31)
    ch = f"{ch:x}".zfill(2).upper()
    return (n, ch)


# Note: First channel is 1
def get_room_vars(number: int) -> (str, str):
    n = str(3)
    ch = min(max(0, number - 1), 15)
    ch = f"{ch:x}".zfill(2).upper()
    return (n, ch)


def db_to_midi(level) -> int:
    return max(0, int(((level + 48) / 58.0) * 127))


def midi_to_db(val) -> float:
    if val == 0:
        return float("-inf")
    return ((val / 127.0) * 58) - 48


# =================== EXAMPLE USAGE ====================


def example():
    # Note: A&H needs us to specify the version in the MIDI SysEx messages
    #       This means certain things won't work if you get this wrong
    #       Version can be found on the front panel of the AHM
    # Note: You need to use your AHM's IP-Address of course (also found at
    #       the front panel)
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

    # More things are possible, check the above Ahm16-class for more methods


if __name__ == "__main__":
    example()
