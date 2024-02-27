"""Monitors the 2 frequencies for APRS messages."""

try:
    import aprslib
except:
    print("Couldn't import aprslib. Did you install it? See the README.md.")
    raise

import curses
import dataclasses
import datetime
import itertools
import math
import multiprocessing
import subprocess
import time
import typing


CALL_SIGN = "KE0FZV"
OFFSET_S = 4 * 60 + 10


@dataclasses.dataclass
class AprsMessage:

    # Example parsed:
    # {'altitude': 12450.7752,
    #  'comment': 'Xa',
    #  'format': 'compressed',
    #  'from': 'M0XER-4',
    #  'gpsfixstatus': 1,
    #  'latitude': 64.11987367625208,
    #  'longitude': -19.070654142799384,
    #  'messagecapable': False,
    #  'path': ['TF3RPF', 'WIDE2*', 'qAR', 'TF3SUT-2'],
    #  'raw': 'M0XER-4>APRS64,TF3RPF,WIDE2*,qAR,TF3SUT-2:!/.(M4I^C,O `DXa/A=040849|#B>@"v90!+|',
    #  'symbol': 'O',
    #  'symbol_table': '/',
    #  'telemetry': {'bits': '00000000',
    #                'seq': 215,
    #                'vals': [2670, 176, 2199, 10, 0]},
    #  'to': 'APRS64',
    # 'via': 'TF3SUT-2'}
    parsed_message: dict
    timestamp: datetime.datetime


@dataclasses.dataclass
class Status:
    frequency_hz: int = 144390000
    messages: typing.List[AprsMessage] = dataclasses.field(default_factory=list)
    last_call_sign_timestamp: typing.Optional[datetime.datetime] = None
    monitor_start: datetime.datetime = dataclasses.field(default_factory=lambda: datetime.datetime.now())
    overall_start: datetime.datetime = dataclasses.field(default_factory=lambda: datetime.datetime.now())
    error: typing.Optional[str] = None
    error_timestamp: typing.Optional[datetime.datetime] = None


def initialize_screen():
    """Initialize a screen."""
    stdscr = curses.initscr()
    # Don't echo keypresses
    curses.noecho()
    # Process keys instantly, instead of waiting for enter
    curses.cbreak()
    # Use special values for keys, e.g. curses.KEY_LEFT, instead of multibyte escape sequences
    stdscr.keypad(True)
    return stdscr


def end_screen(stdscr):
    """End a screen."""
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


def update_screen(
    stdscr,
    status: Status,
) -> None:
    stdscr.clear()

    # Balloon status
    labels = (
        "Latitude:",
        "Longitude:",
        "Altitude:",
        "Vertical:",
        "Course:",
        "Reported Horizontal:",
        "Computed Horizontal:",
        "Estimated altitude:",
        "Last seen:",
        "Satellites:",
        "Voltage:",
        "Temperature:",
        "Frequency:",
    )
    for y, label in enumerate(labels):
        stdscr.addstr(y + 1, 0, label)

    if status.error:
        formatted = datetime.datetime.strftime(status.error_timestamp, "%H:%M:%S")
        stdscr.addstr(0, 0, formatted)
        stdscr.addstr(0, len(formatted), status.error)

    recent = None
    recent2 = None
    recent_rs41 = None
    for message_index in range(len(status.messages) - 1, -1, -1):
        message = status.messages[message_index]
        if CALL_SIGN in message.parsed_message["from"]:
            if not recent:
                recent = message
            elif not recent2:
                recent2 = message

            if not recent_rs41 and message.parsed_message["comment"].startswith("S"):
                recent_rs41 = message
            
            if recent and recent2 and recent_rs41:
                break

    if recent:
        timestamp = recent.timestamp
        msg = recent.parsed_message

        stdscr.addstr(1, len(labels[0]) + 1, f"{msg['latitude']:.4f}")
        stdscr.addstr(2, len(labels[1]) + 1, f"{msg['longitude']:.4f}")
        stdscr.addstr(3, len(labels[2]) + 1, f"{int(msg['altitude'])} m")
        stdscr.addstr(5, len(labels[4]) + 1, f"{int(msg['course'])}°")
        reported_horizontal_ms = msg["speed"] * 1000 / 3600
        stdscr.addstr(6, len(labels[5]) + 1, f"{reported_horizontal_ms:.1f} m/s")
        seconds_ago = (datetime.datetime.now() - timestamp).total_seconds()
        stdscr.addstr(9, len(labels[8]) + 1, f"{int(seconds_ago)}s ago")

    if recent2:
        msg2 = recent2.parsed_message
        horizontal_delta_m = distance(msg["latitude"], msg["longitude"], msg2["latitude"], msg2["longitude"])
        vertical_delta_m = msg2["altitude"] - msg["altitude"]
        seconds = (recent2.timestamp - recent.timestamp).total_seconds()
        horizontal_ms = horizontal_delta_m / seconds
        vertical_ms = vertical_delta_m / seconds
        stdscr.addstr(4, len(labels[3]) + 1, f"{vertical_ms:.1f} m/s")
        stdscr.addstr(7, len(labels[6]) + 1, f"{horizontal_ms:.1f} m/s")

    for message_index in range(0, 10):
        if message_index >= len(status.messages):
            break
        message = status.messages[-message_index - 1]
        formatted = datetime.datetime.strftime(message.timestamp, "%H:%M:%S")
        y = len(labels) + 2 + message_index
        attributes = 0 
        if CALL_SIGN in message.parsed_message["from"]:
            attributes = curses.A_BOLD
        stdscr.addstr(y, 0, formatted, attributes)
        stdscr.addstr(y, len(formatted) + 1, message.parsed_message["raw"], attributes)

    stdscr.refresh()


def curses_main(stdscr) -> None:
    initialize_screen()
    main(stdscr, TestReceiver)
    # main(stdscr, MessageReceiver)


def main(stdscr, receiver_class) -> None:
    status = Status()

    frequencies = (144390000, 432560000)
    timeout_s = 60 * 5
    frequency_index = 0

    while True:
        # Wait for a message on this frequency from KE0FZV
        start = datetime.datetime.now()
        status.monitor_start = start
        frequency_hz = frequencies[frequency_index]
        status.frequency_hz = frequency_hz
        frequency_index = (frequency_index + 1) % len(frequencies)
        parent_pipe, child_pipe = multiprocessing.Pipe()
        receiver = receiver_class(frequency_hz, child_pipe)
        receiver.start()
        found_call_sign = False

        while (datetime.datetime.now() - start).total_seconds() < timeout_s and not found_call_sign:
            try:
                data_waiting = parent_pipe.poll(0.5)
                if data_waiting:
                    raw_message = parent_pipe.recv()
                    parsed = aprslib.parse(raw_message)

                    status.messages.append(AprsMessage(parsed, datetime.datetime.now()))
                    if CALL_SIGN in parsed["from"]:
                        # Found my message! Let's switch to the other frequency
                        found_call_sign = True
                        break

                update_screen(stdscr, status)

            except Exception as exc:
                status.error = str(exc)
                status.error_timestamp = datetime.datetime.now()
                break

        update_screen(stdscr, status)
        receiver.terminate()
        receiver.join()

        if (datetime.datetime.now() - start).total_seconds() > timeout_s:
            # TODO: Warn that it took too long
            pass


class MessageReceiver(multiprocessing.Process):
    def __init__(self, frequency_hz: int, pipe):
        super().__init__()
        self.frequency_hz = frequency_hz
        self.pipe = pipe

    def run(self) -> None:
        rtl_fm = subprocess.Popen(
            ("rtl_fm", "-f", str(self.frequency_hz), "-p", "0", "-"),
            stdout=subprocess.PIPE,
        )
        direwolf = subprocess.Popen(
            ("direwolf", "-c", "sdr.conf", "-r", "24000", "-D", "1", "-t", "0", "-l", ".", "-"),
            stdin=rtl_fm.stdout,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        while True:
            line = direwolf.stdout.readline()
            if "audio level" in line:
                # The next line should have the APRS message
                raw_message = " ".join(direwolf.stdout.readline().split(" ")[1:])
                self.pipe.write(raw_message)


altitude = [5280]
class TestReceiver(multiprocessing.Process):
    def __init__(self, _: int, pipe):
        super().__init__()
        self.pipe = pipe

    def run(self) -> None:
        while self.is_alive():
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                # This will happen when the parent terminates the process
                return

            import random
            if random.randint(0, 10) == 0:
                callsign = f"KE{random.randint(0, 3)}FZV"
                global altitude
                message = f"{callsign}-11>APZ41N:!4000.00N/10500.00WO302/001/A={altitude[0]:06}/S6T28V2455C00"
                altitude[0] += random.randint(0, 4)
                self.pipe.send(message)
                time.sleep(1)


def distance(lat1, long1, lat2, long2):
    """Great circle distance."""
    radius_m = 6371 * 1000
    lat_delta_r = math.radians(lat2 - lat1)
    long_delta_r = math.radians(long2 - long1);
    a = (
        math.sin(lat_delta_r / 2) ** 2 +
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
        math.sin(long_delta_r / 2) * math.sin(long_delta_r / 2)
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_m * c


if __name__ == "__main__":
    #print(aprslib.parse("KE0FZV-11>APZ41N:!3959.88N/10513.71WO302/001/A=005326/S6T28V2455C00"))
    curses.wrapper(curses_main)
