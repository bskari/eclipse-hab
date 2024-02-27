"""Monitors the 2 frequencies for APRS messages."""

try:
    import aprslib
except:
    print("Couldn't import aprslib. Did you install it? See the README.md.")
    raise

import curses
import copy
import dataclasses
import datetime
import math
import multiprocessing
import re
import subprocess
import time
import typing


CALL_SIGN = "KE0FZV"
OFFSET_S = 4 * 60 + 10
# Balloon status
STATUS_LABELS_COUNT = 13


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
    last_call_sign_timestamp: datetime.datetime = None
    monitor_start: datetime.datetime = dataclasses.field(default_factory=lambda: datetime.datetime.now())
    overall_start: datetime.datetime = dataclasses.field(default_factory=lambda: datetime.datetime.now())
    error: str = None
    error_timestamp: datetime.datetime = None


def update_error(window, status: Status) -> None:
    if status.error:
        formatted = datetime.datetime.strftime(status.error_timestamp, "%H:%M:%S")
        window.addstr(1, 1, f"{formatted} {status.error}")
        window.border()
        window.refresh()


def update_status(window, status: Status) -> None:
    recent: AprsMessage = None
    recent2: AprsMessage = None
    recent_rs41: AprsMessage = None
    for message_index in range(len(status.messages) - 1, -1, -1):
        message = status.messages[message_index]
        if CALL_SIGN in message.parsed_message["from"]:
            if not recent:
                recent = message
            elif not recent2:
                recent2 = message

            if not recent_rs41 and message.parsed_message["to"] == "APZ41N":
                recent_rs41 = message

            if recent and recent2 and recent_rs41:
                break

    # Fudge data so that the screen still gets rendered
    dummy = AprsMessage(
        {"latitude": 0, "longitude": 0, "altitude": 0, "course": 0, "speed": 0, "comment": "S0T0V0"},
        timestamp=datetime.datetime.now() - datetime.timedelta(seconds=60 * 60 * 24),
    )
    if not recent:
        recent = dummy
    if not recent2:
        recent2 = copy.deepcopy(dummy)
        recent2.timestamp = recent2.timestamp - datetime.timedelta(seconds=60 * 60 * 24)
    if not recent_rs41:
        recent_rs41 = dummy

    timestamp = recent.timestamp
    msg = recent.parsed_message
    msg2 = recent2.parsed_message
    horizontal_delta_m = distance(msg["latitude"], msg["longitude"], msg2["latitude"], msg2["longitude"])
    vertical_delta_m = msg["altitude"] - msg2["altitude"]
    seconds = (recent.timestamp - recent2.timestamp).total_seconds()
    horizontal_ms = horizontal_delta_m / seconds
    vertical_ms = vertical_delta_m / seconds
    reported_horizontal_ms = msg["speed"] * 1000 / 3600
    seconds_ago = (datetime.datetime.now() - timestamp).total_seconds()
    estimated_altitude_m = msg["altitude"] + seconds_ago * vertical_ms
    match = re.search(r"S(\d+)T(\d+)V(\d)+", recent_rs41.parsed_message["comment"])
    if match:
        groups = match.groups()
    else:
        status.error = "No match"
        status.error_timestamp = datetime.datetime.now()

    window.clear()
    window.border()
    window.addstr(1, 1, f"Latitude: {msg['latitude']:.4f}")
    window.addstr(2, 1, f"Longitude: {msg['longitude']:.4f}")
    window.addstr(3, 1, f"Altitude: {msg['altitude']:.1f} m")
    window.addstr(4, 1, f"Estimated altitude: {estimated_altitude_m:.1f} m")
    window.addstr(5, 1, f"Reported course: {int(msg['course'])}°")
    window.addstr(6, 1, f"Computed vertical: {vertical_ms:.1f} m/s")
    window.addstr(7, 1, f"Reported horizontal: {reported_horizontal_ms:.1f} m/s")
    window.addstr(8, 1, f"Computed horizontal: {horizontal_ms:.1f} m/s")
    window.addstr(9, 1, f"Last seen: {int(seconds_ago)}s ago")
    window.addstr(10, 1, f"Satellites: {groups[0]}")
    window.addstr(11, 1, f"Voltage: {groups[1]} V")
    window.addstr(12, 1, f"Temperature: {groups[2]}° C")
    window.addstr(13, 1, f"Frequency: {status.frequency_hz}")

    window.refresh()


previous_message_count = 0
def update_messages(window, status: Status) -> None:
    global previous_message_count
    if previous_message_count == len(status.messages):
        return

    window.clear()
    window.border()
    # Show recent received messages
    for message_index in range(0, 10):
        if message_index >= len(status.messages):
            break
        message = status.messages[-message_index - 1]
        formatted = datetime.datetime.strftime(message.timestamp, "%H:%M:%S")
        attributes = 0 
        if CALL_SIGN in message.parsed_message["from"]:
            attributes = curses.A_BOLD
        window.addstr(message_index + 1, 1, f"{formatted} {message.parsed_message['raw']}", attributes)

    window.refresh()


def update_screen(
    error_window: curses.window,
    status_window: curses.window,
    messages_window: curses.window,
    status: Status,
) -> None:
    update_status(status_window, status)
    update_messages(messages_window, status)
    # update_error should go last so that if updating another window causes an error, it will be
    # displayed
    update_error(error_window, status)


def curses_main(stdscr) -> None:
    main(stdscr, TestReceiver)
    # main(stdscr, MessageReceiver)


def main(stdscr, receiver_class) -> None:
    status = Status()

    frequencies = (144390000, 432560000)
    timeout_s = 60 * 5
    frequency_index = 0

    error_window = curses.newwin(3, curses.COLS, 0, 0)
    status_window_length = 40
    status_window = curses.newwin(STATUS_LABELS_COUNT + 2, status_window_length, 3, 0)
    messages_window = curses.newwin(12, curses.COLS, STATUS_LABELS_COUNT + 5, 0)

    error_window.border()
    status_window.border()
    messages_window.border()

    error_window.refresh()
    status_window.refresh()
    messages_window.refresh()

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

                update_screen(error_window, status_window, messages_window, status)

            except Exception as exc:
                status.error = str(exc)
                status.error_timestamp = datetime.datetime.now()
                break

        update_screen(error_window, status_window, messages_window, status)
        parent_pipe.send("die")
        receiver.join()

        if (datetime.datetime.now() - start).total_seconds() > timeout_s:
            # TODO: Warn that it took too long
            pass


class MessageReceiver(multiprocessing.Process):
    def __init__(self, frequency_hz: int, pipe: multiprocessing.Pipe):
        super().__init__()
        self.frequency_hz: int = frequency_hz
        self.pipe: multiprocessing.Pipe = pipe

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

            if line == "":
                # The other thread will notify us if it's time to shut down
                anything = self.pipe.poll(0.1)
                if anything:
                    rtl_fm.terminate()
                    direwolf.terminate()
                    return

            if "audio level" in line:
                # The next line should have the APRS message
                raw_message = " ".join(direwolf.stdout.readline().split(" ")[1:])
                self.pipe.write(raw_message)


test_receiver_start = datetime.datetime.now()
class TestReceiver(multiprocessing.Process):
    def __init__(self, _: int, pipe: multiprocessing.Pipe):
        super().__init__()
        self.pipe: multiprocessing.Pipe = pipe
    
    def run(self) -> None:
        while True:
            # The other thread will notify us if it's time to shut down
            anything = self.pipe.poll(0.1)
            if anything:
                return

            import random
            if random.randint(0, 10) == 0:
                callsign = f"KE{random.randint(0, 3)}FZV"
                global test_receiver_start
                altitude = int((datetime.datetime.now() - test_receiver_start).total_seconds()) + 5280
                message = f"{callsign}-11>APZ41N:!4000.00N/10500.00WO302/001/A={altitude:06}/S6T28V2455C00"
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


def debug_log(message: str) -> None:
    formatted = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
    with open("debug.txt", "a") as file:
        file.write(formatted + ":" + message + "\n")


if __name__ == "__main__":
    #print(aprslib.parse("KE0FZV-11>APZ41N:!3959.88N/10513.71WO302/001/A=005326/S6T28V2455C00"))
    curses.wrapper(curses_main)
