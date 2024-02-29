"""Monitors the 2 frequencies for APRS messages."""

import copy
import csv
import curses
import dataclasses
import datetime
import io
import math
import multiprocessing
import multiprocessing.connection
import re
import subprocess
import time
import typing


CALL_SIGN = "KE0FZV"
OFFSET_S = 4 * 60 + 10
# Balloon status
STATUS_LABELS_COUNT = 14
FT_PER_M = 3.2808399
MPH_PER_MPS = 2.2369363

@dataclasses.dataclass
class AprsMessage:
    call_sign: str
    altitude_m: float
    latitude_d: float
    longitude_d: float
    course_d: float
    horizontal_speed_mps: float
    symbol: str
    comment: str
    frequency_hz: int
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


def update_error(window, status: Status) -> None:
    if status.error and status.error_timestamp:
        formatted = datetime.datetime.strftime(status.error_timestamp, "%H:%M:%S")
        window.addstr(1, 1, f"{formatted} {status.error}")
        window.border()
        window.refresh()


def update_status(window, status: Status) -> None:
    recent: typing.Optional[AprsMessage] = None
    recent2: typing.Optional[AprsMessage] = None
    recent_rs41: typing.Optional[AprsMessage] = None
    launch_site: typing.Optional[AprsMessage] = None

    for message_index in range(len(status.messages) - 1, -1, -1):
        message = status.messages[message_index]
        if CALL_SIGN in message.call_sign:
            if not recent:
                recent = message
            elif not recent2:
                recent2 = message

            if not recent_rs41 and message.frequency_hz == 432560000:
                recent_rs41 = message

            if recent and recent2 and recent_rs41:
                break

    # Assume that the first message from us is the launch site's location
    for message in status.messages:
        if CALL_SIGN in message.call_sign:
            launch_site = message
            break

    # Fudge data so that the screen still gets rendered
    dummy = AprsMessage(
        call_sign="KE0FZV-11",
        altitude_m=0.0,
        latitude_d=0.0,
        longitude_d=0.0,
        course_d=0.0,
        horizontal_speed_mps=0.0,
        symbol="O",
        comment="/S0T0V0001C00 dummy message",
        frequency_hz=144390000,
        timestamp=datetime.datetime.now() - datetime.timedelta(seconds=60 * 60 * 24),
    )
    if not recent:
        recent = dummy
    if not recent2:
        recent2 = copy.deepcopy(dummy)
        # Fudge the time so that we don't divide by 0 seconds
        recent2.timestamp = recent2.timestamp - datetime.timedelta(seconds=60 * 60 * 24)
    if not recent_rs41:
        recent_rs41 = dummy
    if not launch_site:
        launch_site = dummy

    timestamp = recent.timestamp
    msg = recent
    msg2 = recent2
    distance_km = distance_m(msg.latitude_d, msg.longitude_d, launch_site.latitude_d, launch_site.longitude_d) / 1000
    horizontal_delta_m = distance_m(msg.latitude_d, msg.longitude_d, msg2.latitude_d, msg2.longitude_d)
    vertical_delta_m = msg.altitude_m - msg2.altitude_m
    seconds = (recent.timestamp - recent2.timestamp).total_seconds()
    horizontal_ms = horizontal_delta_m / seconds
    vertical_ms = vertical_delta_m / seconds
    reported_horizontal_ms = msg.horizontal_speed_mps * 1000 / 3600
    seconds_ago = (datetime.datetime.now() - timestamp).total_seconds()
    estimated_altitude_m = msg.altitude_m + seconds_ago * vertical_ms
    match = re.search(r"S(\d+)T(\d+)V(\d+)", recent_rs41.comment)
    if match:
        groups = match.groups()
        satellite_count = int(groups[0])
        temperature_c = int(groups[1])
        battery_v = float(groups[2]) / 1000
    else:
        status.error = f"Unable to parse comment field {recent_rs41.comment}"
        status.error_timestamp = datetime.datetime.now()
        satellite_count = 0
        battery_v = 0.0
        temperature_c = 0

    window.clear()
    window.border()
    window.addstr(1, 1, f"Latitude: {msg.latitude_d:.4f}")
    window.addstr(2, 1, f"Longitude: {msg.longitude_d:.4f}")
    window.addstr(3, 1, f"Distance: {distance_km:.2f} km, {distance_km * 0.62137119:.2f} mi")
    window.addstr(4, 1, f"Altitude: {msg.altitude_m:.1f} m, {msg.altitude_m * FT_PER_M:.1f} ft")
    window.addstr(5, 1, f"Est. alt.: {estimated_altitude_m:.1f} m, {estimated_altitude_m * FT_PER_M:.1f} ft")
    window.addstr(6, 1, f"Reported course: {int(msg.course_d)}°")
    window.addstr(7, 1, f"Computed vert.: {vertical_ms:.1f} m/s, {vertical_ms * FT_PER_M:.1f} ft/s")
    window.addstr(8, 1, f"Reported horiz.: {reported_horizontal_ms:.1f} m/s, {reported_horizontal_ms * MPH_PER_MPS:.1f} mph")
    window.addstr(9, 1, f"Computed horiz.: {horizontal_ms:.1f} m/s, {horizontal_ms * MPH_PER_MPS:.1f} mph")
    window.addstr(10, 1, f"Last seen: {int(seconds_ago)} s ago")
    window.addstr(11, 1, f"Satellites: {satellite_count}")
    window.addstr(12, 1, f"Voltage: {battery_v:.3f} V")
    window.addstr(13, 1, f"Temperature: {temperature_c}°C, {temperature_c * 1.8 + 32:.0f}°F")
    window.addstr(14, 1, f"Monitoring: {status.frequency_hz} hz")

    window.refresh()


previous_message_count = 0
def update_messages(window: curses.window, status: Status) -> None:
    global previous_message_count
    if previous_message_count == len(status.messages):
        return

    window.clear()
    window.border()
    max_y, max_x = window.getmaxyx()
    # Show recent received messages
    for message_index in range(0, max_y - 2):
        if message_index >= len(status.messages):
            break
        msg = status.messages[-message_index - 1]
        timestamp = datetime.datetime.strftime(msg.timestamp, "%H:%M:%S")
        attributes = 0 
        if CALL_SIGN in msg.call_sign:
            attributes = curses.A_BOLD
        formatted = f"{msg.call_sign} {msg.latitude_d:.4f} {msg.longitude_d:.4f} {msg.altitude_m:.1f}m {msg.symbol} {msg.comment}"
        whole = f"{timestamp} {formatted}"
        window.addnstr(message_index + 1, 1, whole, max_x - 2, attributes)

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
    # main(stdscr, TestReceiver)
    main(stdscr, MessageReceiver)


def main(stdscr, receiver_class) -> None:
    status = Status()

    frequencies_hz = (144390000, 432560000)
    timeout_s = 60 * 5
    frequency_index = 1

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
        frequency_hz = frequencies_hz[frequency_index]
        status.frequency_hz = frequency_hz
        parent_pipe, child_pipe = multiprocessing.Pipe()
        debug_log(f"Starting a new receiver class {frequency_hz}")
        receiver = receiver_class(frequency_hz, child_pipe)
        receiver.start()
        debug_log("Started")
        found_call_sign = False

        while (datetime.datetime.now() - start).total_seconds() < timeout_s and not found_call_sign:
            try:
                update_screen(error_window, status_window, messages_window, status)
                data_waiting = parent_pipe.poll(0.5)
                if data_waiting:
                    csv_message = parent_pipe.recv()
                    if not csv_message:
                        continue
                    debug_log(f"{csv_message=}")
                    #parsed = aprslib.parse(raw_message)
                    field_names = "chan,utime,isotime,source,heard,level,error,dti,name,symbol,latitude,longitude,speed,course,altitude,frequency,offset,tone,system,status,telemetry,comment".split(",")
                    fake_file = io.StringIO(csv_message)
                    reader = csv.DictReader(fake_file, fieldnames=field_names, delimiter=",")
                    for _row in reader:
                        print(_row)
                        row = _row

                    status.messages.append(
                        AprsMessage(
                            call_sign=row["source"],
                            altitude_m=float(row["altitude"]),
                            latitude_d=float(row["latitude"]),
                            longitude_d=float(row["longitude"]),
                            course_d=float(row["course"]),
                            horizontal_speed_mps=float(row["speed"]),
                            symbol=row["symbol"],
                            comment=row["comment"],
                            frequency_hz=frequency_hz,
                            timestamp=datetime.datetime.now(),
                        )
                    )
                    if CALL_SIGN in row["source"]:
                        # Found my message! Let's switch to the other frequency
                        found_call_sign = True
                        break

            except Exception as exc:
                status.error = str(exc)
                status.error_timestamp = datetime.datetime.now()
                break

        update_screen(error_window, status_window, messages_window, status)
        debug_log("Sending die")
        parent_pipe.send("die")
        debug_log("Calling join")
        receiver.join()
        debug_log("Joined")

        frequency_index = (frequency_index + 1) % len(frequencies_hz)

        if (datetime.datetime.now() - start).total_seconds() > timeout_s:
            status.error = "Timed out waiting for message on frequency_hz"
            status.error_timestamp = datetime.datetime.now()


class MessageReceiver(multiprocessing.Process):
    def __init__(self, frequency_hz: int, pipe: multiprocessing.connection.Connection):
        super().__init__()
        self.frequency_hz: int = frequency_hz
        self.pipe: multiprocessing.connection.Connection = pipe

    def run(self) -> None:
        file_name = "aprs.log"
        command = " ".join(("rtl_fm", "-f", str(self.frequency_hz), "-p", "0", "-"))
        debug_log(f"Running {command}")
        rtl_fm = subprocess.Popen(
            ("rtl_fm", "-f", str(self.frequency_hz), "-p", "0", "-"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        direwolf = subprocess.Popen(
            ("direwolf", "-c", "sdr.conf", "-r", "24000", "-D", "1", "-t", "0", "-L", file_name, "-"),
            stdin=rtl_fm.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )

        previous_line = tail_file(file_name)
        while True:
            # The other thread will notify us if it's time to shut down
            anything = self.pipe.poll(0.1)
            if anything:
                debug_log("Calling terminate and wait")
                rtl_fm.terminate()
                rtl_fm.communicate()
                rtl_fm.wait()
                direwolf.terminate()
                direwolf.communicate()
                direwolf.wait()
                debug_log("Done calling terminate and wait")
                return

            # I can't figure out how to read the lines from Direwolf that show the parsed messages.
            # I can read from stdin and get the audio level messages, but not the APRS message?
            # Doesn't look like it's coming from stderr. So, let's just read from the log file.
            line = tail_file(file_name)

            if line == previous_line:
                continue
        
            if not line.startswith("chan"):
                # Just send the CSV message and let them deal with it?
                self.pipe.send(line)


test_receiver_start = datetime.datetime.now()
class TestReceiver(multiprocessing.Process):
    def __init__(self, _: int, pipe: multiprocessing.connection.Connection):
        super().__init__()
        self.pipe: multiprocessing.connection.Connection = pipe
    
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
                # TODO: This is wrong now, I had to rework stuff to work with Direwolf. It should be
                # sending a CSV line. Ugh.
                message = f"{callsign}-11>APZ41N:!4000.00N/10500.00WO302/001/A={altitude:06}/S6T28V2455C00"
                self.pipe.send(message)
                time.sleep(1)


def distance_m(lat1: float, long1: float, lat2: float, long2: float) -> float:
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


def tail_file(file_name: str) -> str:
    """Returns the last line of a file."""
    try:
        with open(file_name, "r"):
            pass
    except FileNotFoundError:
        debug_log(f"Unable to tail_file {file_name} because not found")
        return ""

    process = subprocess.Popen(
        ("tail", "-n", "1", file_name),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    # Mypy thinks this might be None?
    if process.stdout == None:
        debug_log("tail_file has None process.stdout?")
        return ""
    
    return process.stdout.readline().decode()


def debug_log(message: str) -> None:
    formatted = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
    with open("debug.log", "a") as file:
        file.write(formatted + ":" + message)
        if not message.endswith("\n"):
            file.write("\n")


if __name__ == "__main__":
    #print(aprslib.parse("KE0FZV-11>APZ41N:!3959.88N/10513.71WO302/001/A=005326/S6T28V2455C00"))
    curses.wrapper(curses_main)
