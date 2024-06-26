"""Monitors the 2 frequencies for APRS messages."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import aprs_symbols
import argparse
import aprslib
import copy
import csv
import curses
import dataclasses
import datetime
import fcntl
import io
import logging
import math
import multiprocessing
import multiprocessing.connection
import os
import random
import re
import subprocess
import threading
import time
import typing


OFFSET_S = 4 * 60 + 10
# Balloon status
STATUS_LABELS_COUNT = 14
FT_PER_M = 3.2808399
MPH_PER_MPS = 2.2369363
MILES_PER_KM = 0.62137119

logger = logging.getLogger(__file__)

@dataclasses.dataclass
class AprsMessage:
    call_sign: str
    altitude_m: float
    latitude_d: float
    longitude_d: float
    course_d: float
    horizontal_speed_mps: float
    symbol: str
    symbol_table: str
    comment: str
    frequency_hz: int
    timestamp: datetime.datetime
    aprs_message: str


DUMMY_APRS_MESSAGE = AprsMessage(
    call_sign="KE0FZV-11",
    altitude_m=0.0,
    latitude_d=0.0,
    longitude_d=0.0,
    course_d=0.0,
    horizontal_speed_mps=0.0,
    symbol="O",
    symbol_table="/",
    comment="/S0T0V0001C00 dummy message",
    frequency_hz=144390000,
    timestamp=datetime.datetime.now() - datetime.timedelta(seconds=60 * 60 * 24),
    aprs_message="",
)


@dataclasses.dataclass
class Status:
    my_call_sign: str
    frequency_hz: int = 144390000
    messages: typing.List[AprsMessage] = dataclasses.field(default_factory=list)
    last_call_sign_timestamp: typing.Optional[datetime.datetime] = None
    monitor_start: datetime.datetime = dataclasses.field(default_factory=lambda: datetime.datetime.now())
    overall_start: datetime.datetime = dataclasses.field(default_factory=lambda: datetime.datetime.now())
    falling: bool = False
    test: bool = False


@dataclasses.dataclass
class Options:
    call_sign: str
    interval_s: float
    aprs_only: bool
    rs41_only: bool
    test: bool


@dataclasses.dataclass
class Windows:
    time: curses.window
    error: curses.window
    status: curses.window
    messages: curses.window
    stations: curses.window


class CursesHandler(logging.Handler):
    def __init__(self, error_window: curses.window):
        super().__init__()
        self.window: curses.window = error_window

    def emit(self, record: logging.LogRecord):
        formatted = self.format(record)
        setattr(update_error, "timestamp", datetime.datetime.now())
        setattr(update_error, "level", record.levelno)
        setattr(update_error, "formatted", formatted)
        update_error(self.window)


def update_status(window: curses.window, status: Status) -> None:
    if not hasattr(update_status, "recent_id"):
        setattr(update_status, "recent_id", None)

    recent: typing.Optional[AprsMessage] = None
    recent2: typing.Optional[AprsMessage] = None
    recent_rs41: typing.Optional[AprsMessage] = None
    launch_site = get_launch_site(status)

    for message_index in range(len(status.messages) - 1, -1, -1):
        message = status.messages[message_index]
        if status.my_call_sign in message.call_sign:
            if not recent:
                recent = message
            elif not recent2:
                recent2 = message

            if not recent_rs41 and message.frequency_hz == 432560000:
                recent_rs41 = message

            if recent and recent2 and recent_rs41:
                break

    # Fudge data so that the screen still gets rendered
    if not recent:
        recent = DUMMY_APRS_MESSAGE
    if not recent2:
        recent2 = copy.deepcopy(DUMMY_APRS_MESSAGE)
        # Fudge the time so that we don't divide by 0 seconds
        recent2.timestamp = recent2.timestamp - datetime.timedelta(seconds=60 * 60 * 24)
    if not recent_rs41:
        recent_rs41 = DUMMY_APRS_MESSAGE

    # If there's not a new message, then we only need to update the seconds ago and estimates
    timestamp = recent.timestamp
    seconds_ago = (datetime.datetime.now() - timestamp).total_seconds()
    vertical_delta_m = recent.altitude_m - recent2.altitude_m
    seconds = (recent.timestamp - recent2.timestamp).total_seconds()
    vertical_ms = vertical_delta_m / seconds
    estimated_altitude_m = recent.altitude_m + seconds_ago * vertical_ms
    _, max_x = window.getmaxyx()
    window.move(5, 1)
    window.clrtoeol()
    window.addnstr(5, 1, f"Est. alt.: {estimated_altitude_m:.1f} m, {estimated_altitude_m * FT_PER_M:.1f} ft", max_x - 2)
    window.move(10, 1)
    window.clrtoeol()
    isecs = int(seconds_ago)
    ago = f"{isecs // 3600:02}:{(isecs // 60) % 60:02}:{isecs % 60:02}"
    window.addnstr(10, 1, f"Last seen: {ago} ago", max_x - 2)
    window.move(14, 1)
    window.clrtoeol()
    window.addnstr(14, 1, f"Monitoring: {status.frequency_hz} hz", max_x - 2)
    window.border()

    # If there's not a new message, then we only need to update the seconds ago and estimates
    if update_status.recent_id == id(recent):  # type: ignore
        window.noutrefresh()
        return

    update_status.recent_id = id(recent)  # type: ignore

    distance_km = distance_m(recent.latitude_d, recent.longitude_d, launch_site.latitude_d, launch_site.longitude_d) / 1000
    horizontal_delta_m = distance_m(recent.latitude_d, recent.longitude_d, recent2.latitude_d, recent2.longitude_d)
    horizontal_ms = horizontal_delta_m / seconds
    reported_horizontal_ms = recent.horizontal_speed_mps * 1000 / 3600
    match = re.search(r"S(\d+)T(\d+)V(\d+)", recent_rs41.comment)
    if match:
        groups = match.groups()
        satellite_count = int(groups[0])
        temperature_c = int(groups[1])
        battery_v = float(groups[2]) / 1000
    else:
        logger.error("Unable to parse comment field %s", recent_rs41.comment)
        satellite_count = 0
        battery_v = 0.0
        temperature_c = 0

    if vertical_ms < -2.0 and recent.altitude_m > 3000 and not status.falling:
        status.falling = True
        logger.critical("Payload is falling!")

    window.clear()
    window.border()
    window.addnstr(1, 1, f"Latitude: {recent.latitude_d:.4f}", max_x - 2)
    window.addnstr(2, 1, f"Longitude: {recent.longitude_d:.4f}", max_x - 2)
    window.addnstr(3, 1, f"Distance: {distance_km:.2f} km, {distance_km * MILES_PER_KM:.2f} mi", max_x - 2)
    window.addnstr(4, 1, f"Altitude: {recent.altitude_m:.1f} m, {recent.altitude_m * FT_PER_M:.1f} ft", max_x - 2)
    window.addnstr(5, 1, f"Est. alt.: {estimated_altitude_m:.1f} m, {estimated_altitude_m * FT_PER_M:.1f} ft", max_x - 2)
    window.addnstr(6, 1, f"Reported course: {int(recent.course_d)}°", max_x - 2)
    window.addnstr(7, 1, f"Computed vert.: {vertical_ms:.1f} m/s, {vertical_ms * FT_PER_M:.1f} ft/s", max_x - 2)
    window.addnstr(8, 1, f"Reported horiz.: {reported_horizontal_ms:.1f} m/s, {reported_horizontal_ms * MPH_PER_MPS:.1f} mph", max_x - 2)
    window.addnstr(9, 1, f"Computed horiz.: {horizontal_ms:.1f} m/s, {horizontal_ms * MPH_PER_MPS:.1f} mph", max_x - 2)
    ago = f"{isecs // 3600:02}:{(isecs // 60) % 60:02}:{isecs % 60:02}"
    window.addnstr(10, 1, f"Last seen: {ago} ago", max_x - 2)
    window.addnstr(11, 1, f"Satellites: {satellite_count}", max_x - 2)
    window.addnstr(12, 1, f"Voltage: {battery_v:.3f} V", max_x - 2)
    window.addnstr(13, 1, f"Temperature: {temperature_c}°C, {temperature_c * 1.8 + 32:.0f}°F", max_x - 2)
    window.addnstr(14, 1, f"Monitoring: {status.frequency_hz} hz", max_x - 2)

    window.noutrefresh()


def update_messages(window: curses.window, status: Status) -> None:
    """Show recently received APRS packets."""
    if not hasattr(update_messages, "previous_message_count"):
        setattr(update_messages, "previous_message_count", 0)
    if update_messages.previous_message_count == len(status.messages):  # type: ignore
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
        if status.my_call_sign in msg.call_sign:
            attributes = curses.A_BOLD
        whole = f"{timestamp} {msg.aprs_message}"
        window.addnstr(message_index + 1, 1, whole, max_x - 2, attributes)

    setattr(update_messages, "previous_message_count", len(status.messages))
    window.noutrefresh()


def update_stations(window: curses.window, status: Status) -> None:
    """Show the most recent stations received."""
    if not hasattr(update_stations, "previous_recents"):
        setattr(update_stations, "previous_recents", [])

    max_y, max_x = window.getmaxyx()
    now = datetime.datetime.now()

    station_to_message: typing.Dict[str, AprsMessage] = dict()
    for message in status.messages:
        station_to_message[message.call_sign] = message
    recents: typing.List[AprsMessage] = sorted(station_to_message.values(), key=lambda m: m.timestamp, reverse=True)
    previous_recents = getattr(update_stations, "previous_recents")
    # If there are no new stations, just update the seconds
    if recents == previous_recents:
        # Just need to update the seconds
        for count, msg in enumerate(recents):
            seconds = int((now - msg.timestamp).total_seconds())
            ago = f"{seconds // 3600:02}:{(seconds // 60) % 60:02}:{seconds % 60:02}"
            window.addnstr(1 + count, 11, ago, max_x - 3)
        window.noutrefresh()
        return

    # Otherwise, just refresh it all
    setattr(update_stations, "previous_recents", recents)
    window.clear()
    window.border()

    launch_site = get_launch_site(status)
    for count, msg in enumerate(recents):
        distance_km = distance_m(launch_site.latitude_d, launch_site.longitude_d, msg.latitude_d, msg.longitude_d) / 1000
        seconds = int((now - msg.timestamp).total_seconds())
        ago = f"{seconds // 3600:02}:{(seconds // 60) % 60:02}:{seconds % 60:02}"
        unicode_symbol = aprs_symbols.get_symbol(msg.symbol_table, msg.symbol)
        info = f"{msg.call_sign:9} {ago} ago {msg.latitude_d:8.4f} {msg.longitude_d:9.4f} {distance_km:7.2f}km {msg.altitude_m:7.1f}m {unicode_symbol} {msg.comment}"
        # Do max_x - 3 instead of max_x - 2 because Unicode emojis are not the same size
        window.addnstr(1 + count, 1, info, max_x - 3)
        if count + 2 > max_y:
            break
    window.noutrefresh()


def update_error(window: curses.window) -> None:
    if hasattr(update_error, "formatted"):
        level: int = getattr(update_error, "level")
        timestamp: datetime.datetime = getattr(update_error, "timestamp")
        formatted: str = getattr(update_error, "formatted") or "(none)"
    else:
        return

    attributes = 0
    seconds_ago = (datetime.datetime.now() - timestamp).total_seconds()
    fade_s = 60 * 2
    bold_s = 60
    if seconds_ago > fade_s + 10:
        # It's already been updated
        return
    if seconds_ago > fade_s:
        attributes |= curses.A_DIM
    elif seconds_ago < bold_s:
        attributes |= curses.A_BOLD

    color_index = 0
    if seconds_ago <= fade_s and level in (logging.ERROR, logging.CRITICAL):
        color_index = 1

    _, max_x = window.getmaxyx()
    window.clear()
    window.border()
    window.addnstr(1, 1, formatted.split("\n")[0], max_x - 2, attributes | curses.color_pair(color_index))
    window.noutrefresh()


def update_time(window: curses.window) -> None:
    formatted = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
    _, max_x = window.getmaxyx()
    window.addnstr(1, 1, formatted, max_x - 2)
    window.noutrefresh()


def update_screen(windows: Windows, status: Status) -> None:
    update_status(windows.status, status)
    update_messages(windows.messages, status)
    update_stations(windows.stations, status)
    update_error(windows.error)
    update_time(windows.time)
    curses.doupdate()


def report_to_google_earth(status: Status) -> None:
    with open("aprs.kml", "w") as file:
        file.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Paths</name>
    <Placemark>
      <name>{status.my_call_sign} APRS</name>
      <description>{status.my_call_sign} weather balloon APRS</description>
      <Style>
        <LineStyle>
          <color>7f00ffff</color>
          <width>4</width>
        </LineStyle>
        <PolyStyle>
          <color>7f00ff00</color>
        </PolyStyle>
      </Style>
      <LineString>
        <extrude>1</extrude>
        <tessellate>1</tessellate>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>\n""")
        for message in status.messages:
            if status.my_call_sign in message.call_sign:
                file.write(f"{message.longitude_d},{message.latitude_d},{message.altitude_m}\n")
        file.write("""        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>""")


def get_launch_site(status: Status) -> AprsMessage:
    """Return the assumed launch site."""
    if hasattr(get_launch_site, "launch_site"):
        return get_launch_site.launch_site  # type: ignore
    # Assume that the first message from us is the launch site's location
    for message in status.messages:
        if status.my_call_sign in message.call_sign:
            setattr(get_launch_site, "launch_site", message)
            return message
    return DUMMY_APRS_MESSAGE


def format_aprs_message(now: datetime.datetime, frequency_hz: int, raw_message: str) -> AprsMessage:
    try:
        parsed = aprslib.parse(raw_message)
    except aprslib.exceptions.ParseError as exc:
        logger.error("Parsing failed: %s", raw_message, exc_info=exc)
        return ""

    # I guess if speed is 0, aprslib just won't put in the key for it? Ugh
    def get(key: str, type_):
        if key in parsed:
            return type_(parsed[key])
        if type_ == float:
            return 0.0
        if type_ == str:
            return ""
        logger.warning("Unknown type in parse_and_save_message: %s", type_)
        return ""

    return AprsMessage(
        call_sign=get("from", str),
        altitude_m=get("altitude", float),
        latitude_d=get("latitude", float),
        longitude_d=get("longitude", float),
        course_d=get("course", float),
        horizontal_speed_mps=get("speed", float),
        symbol=get("symbol", str),
        symbol_table=get("symbol_table", str),
        comment=get("comment", str),
        frequency_hz=frequency_hz,
        timestamp=now,
        aprs_message=raw_message,
    )


def parse_and_save_message(aprs_message: str, frequency_hz: int, status: Status) -> str:
    """Parse and save a message, and return the call sign and SSID."""
    logger.info("Received APRS message %s", aprs_message)
    now = datetime.datetime.now()

    formatted = format_aprs_message(now, frequency_hz, aprs_message)
    status.messages.append(formatted)

    # Don't save test mode messages
    if not status.test:
        with open("messages.csv", "a") as file:
            writer = csv.writer(file)
            writer.writerow([int(now.timestamp()), frequency_hz, aprs_message])

    return formatted.call_sign


def main(stdscr: curses.window, receiver_class, options: Options) -> None:
    windows = initialize_screen(stdscr)
    initialize_logger(windows)
    loop_forever(windows, receiver_class, options)


def initialize_screen(stdscr: curses.window) -> Windows:
    """Initializes the screen."""
    stdscr.nodelay(True)
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    time_window = curses.newwin(3, 10, 0, 0)
    time_window_x = time_window.getmaxyx()[1]
    error_window = curses.newwin(3, curses.COLS - time_window_x, 0, time_window_x)
    status_window_length = 40
    status_window = curses.newwin(STATUS_LABELS_COUNT + 2, status_window_length, 3, 0)
    lines = curses.LINES - status_window.getmaxyx()[0] - time_window.getmaxyx()[0]
    messages_window = curses.newwin(lines, curses.COLS, STATUS_LABELS_COUNT + 5, 0)
    stations_window = curses.newwin(STATUS_LABELS_COUNT + 2, curses.COLS - status_window_length, 3, status_window_length)

    time_window.border()
    error_window.border()
    status_window.border()
    messages_window.border()
    stations_window.border()

    time_window.refresh()
    error_window.refresh()
    status_window.refresh()
    messages_window.refresh()
    stations_window.refresh()

    return Windows(
        time=time_window,
        error=error_window,
        status=status_window,
        messages=messages_window,
        stations=stations_window,
    )


def initialize_logger(windows: Windows) -> None:
    logger.setLevel(logging.DEBUG)
    handler = CursesHandler(windows.error)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    handler.setLevel(logging.WARN)
    logger.addHandler(handler)
    handler2 = logging.FileHandler("aprs-debug.log")
    handler2.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s:%(lineno)s %(message)s"))
    handler2.setLevel(logging.DEBUG)
    logger.addHandler(handler2)


def load_stations_from_file(status: Status) -> None:
    try:
        count = 0
        with open("messages.csv", "rb") as file:
            try:
                file.seek(-1, os.SEEK_END)
                while count < 20:
                    file.seek(-2, os.SEEK_CUR)
                    while file.read(1) != b"\n":
                        file.seek(-2, os.SEEK_CUR)
                    count += 1
                lines = file.read().decode()
            except OSError:
                # This will happen if there aren't enough lines in the file
                file.seek(0)
                lines = file.read().decode()
                pass
        logger.debug("Found %d old messages from the messages file", count)

        io_lines = io.StringIO(lines)
        count = 0
        reader = csv.reader(io_lines)
        for row in reader:
            unix_timestamp, frequency_hz_str, raw_message = row
            time = datetime.datetime.fromtimestamp(int(unix_timestamp))
            formatted = format_aprs_message(time, int(frequency_hz_str), raw_message)
            status.messages.append(formatted)
            count += 1
        logger.debug("Parsed and added %d old messages from the messages file", count)

    except Exception as exc:
        logger.error("Unable to load previous messages: %s", exc, exc_info=exc)


def loop_forever(windows: Windows, receiver_class, options: Options) -> None:
    logger.debug("Starting")

    my_call_sign = options.call_sign
    interval_s = options.interval_s

    status = Status(my_call_sign=my_call_sign, test=options.test)

    load_stations_from_file(status)

    RS41_FREQUENCY = 432560000
    APRS_FREQUENCY = 144390000

    frequencies_hz: typing.Iterable[int]
    if options.aprs_only:
        frequencies_hz  = (APRS_FREQUENCY,)
    elif options.rs41_only:
        frequencies_hz  = (RS41_FREQUENCY,)
    else:
        #frequencies_hz = (RS41_FREQUENCY, APRS_FREQUENCY)
        frequencies_hz = (APRS_FREQUENCY, RS41_FREQUENCY)

    frequency_index = 0
    next_expected_rs41_time: typing.Optional[datetime.datetime] = datetime.datetime(2024, 4, 8, 17, 38, 11)
    timeout_s = 60 * 5
    # Window on both sides. i.e., seconds before to switch to listen to RS41, seconds after expected
    # to assume we missed it
    rs41_window_s = 10
    interval = datetime.timedelta(seconds=interval_s)
    now = lambda: datetime.datetime.now()

    while True:
        # Wait for a message on this frequency from my call sign
        start = now()
        status.monitor_start = start
        frequency_hz = frequencies_hz[frequency_index]
        status.frequency_hz = frequency_hz
        parent_pipe, child_pipe = multiprocessing.Pipe()
        logger.info("Monitoring %d", frequency_hz)
        receiver = receiver_class(frequency_hz, child_pipe)
        receiver.start()

        # We want to stay on 144.390 MHz as much as possible, because it's fun to see other people
        # broadcasting. Therefore, we want to switch frequencies if:
        # 1) We passed the timeout, or
        # 2) We're listening on 144.390 MHz and we're getting close to the 433.560 MHz broadcast, or
        # 3) We're listening on 433.560 MHz but we missed it
        def passed_timeout() -> bool:
            return (now() - start).total_seconds() > timeout_s
        def approaching_rs41() -> bool:
            return frequency_hz == APRS_FREQUENCY and next_expected_rs41_time is not None and (next_expected_rs41_time - now()).total_seconds() < rs41_window_s
        def missed_rs41() -> bool:
            return frequency_hz == RS41_FREQUENCY and next_expected_rs41_time is not None and (now() - next_expected_rs41_time).total_seconds() > rs41_window_s

        while (
            not passed_timeout() and not approaching_rs41() and not missed_rs41()
        ):
            # Just keep listening and parsing
            try:
                update_screen(windows, status)

                if not receiver.is_alive():
                    logger.error("Receiver quit unexpectedly")
                    # Let's give it half a second so it's not just continually restarting
                    time.sleep(0.5)
                    break

                data_waiting = parent_pipe.poll(0.5)
                if data_waiting:
                    aprs_message = parent_pipe.recv().strip()
                    if not aprs_message:
                        continue
                    ssid = parse_and_save_message(aprs_message, frequency_hz, status)
                    if status.my_call_sign in ssid:
                        # Report to Google Earth
                        try:
                            report_to_google_earth(status)
                        except Exception as exc:
                            logger.debug("Couldn't write to ttyS0", exc_info=exc)

                        # If we're on RS41 and found my message, then switch back to APRS
                        if frequency_hz == RS41_FREQUENCY:
                            if next_expected_rs41_time is None:
                                next_expected_rs41_time = now() + interval
                                logger.debug("Found initial message on %d", frequency_hz)
                            break

            except Exception as exc:
                logger.error(str(exc), exc_info=exc)
                break

        if passed_timeout() or missed_rs41():
            if next_expected_rs41_time:
                formatted = datetime.datetime.strftime(next_expected_rs41_time, "%H:%M:%S")
                logger.warning("Timed out waiting for message on %d, expected %s", frequency_hz, formatted)
            else:
                logger.warning("Timed out waiting for message on %d", frequency_hz)
        elif approaching_rs41():
            if next_expected_rs41_time is not None:
                formatted = datetime.datetime.strftime(next_expected_rs41_time, "%H:%M:%S")
            else:
                formatted = "(none)"
            logger.debug("Approaching the RS41 time: %s", formatted)

        update_screen(windows, status)
        logger.debug("Killing monitor")
        parent_pipe.send("die")
        receiver.join()

        # Update the next expected time
        if next_expected_rs41_time is not None:
            while next_expected_rs41_time < now() + datetime.timedelta(seconds=rs41_window_s):
                next_expected_rs41_time = next_expected_rs41_time + interval
            formatted = datetime.datetime.strftime(next_expected_rs41_time, "%H:%M:%S")
            logger.debug("Next expected RS41 time is %s", formatted)

        frequency_index = (frequency_index + 1) % len(frequencies_hz)


class AprsReceiver(multiprocessing.Process):
    def __init__(self, frequency_hz: int, pipe: multiprocessing.connection.Connection):
        super().__init__()
        self.frequency_hz: int = frequency_hz
        self.pipe: multiprocessing.connection.Connection = pipe

    def run(self) -> None:
        file_name = "aprs.log"
        command = " ".join(("rtl_fm", "-f", str(self.frequency_hz), "-p", "0", "-"))
        logger.debug(f"Running {command}")
        rtl_fm = subprocess.Popen(
            ("rtl_fm", "-f", str(self.frequency_hz), "-p", "0", "-"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        direwolf = subprocess.Popen(
            ("direwolf", "-c", "sdr.conf", "-r", "24000", "-D", "1", "-t", "0", "-L", file_name, "-"),
            stdin=rtl_fm.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )

        # Change it to non-blocking
        assert direwolf.stdout is not None
        descriptor = fcntl.fcntl(direwolf.stdout.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(direwolf.stdout.fileno(), fcntl.F_SETFL, descriptor | os.O_NONBLOCK)

        while True:
            # The other thread will notify us if it's time to shut down
            anything = self.pipe.poll(0.1)
            if anything:
                logger.debug("Calling terminate and wait")
                rtl_fm.terminate()
                rtl_fm.communicate()
                rtl_fm.wait()
                direwolf.terminate()
                direwolf.communicate()
                direwolf.wait()
                logger.debug("Done calling terminate and wait")
                return

            if rtl_fm.poll():
                logger.error("rtl_fm quit unexpectedly")
                return

            try:
                lines = direwolf.stdout.readlines()
                for line in lines:
                    if re.match(r"\[\d", line):
                        aprs_message = " ".join(line.split(" ")[1:])
                        self.pipe.send(aprs_message)
            except IOError:
                continue


test_receiver_start_time = datetime.datetime.now()
class TestReceiver(multiprocessing.Process):
    def __init__(self, _: int, pipe: multiprocessing.connection.Connection):
        super().__init__()
        self.pipe: multiprocessing.connection.Connection = pipe

    def run(self) -> None:
        next = datetime.datetime.now() + datetime.timedelta(seconds=random.randint(1, 10))

        messages = (
            "KE0FZV-11>APZ41N:!4000.00N/10500.00WO111/000/A=005280/S11T34V2317C00",
            "KE0FZV-11>APRS:/222200h4000.00N/10500.00WO000/000/A=005280 Tracksoar",
            "N2XGL-9>S9UYQU,WIDE1-1,WIDE2-1:`q)up7@>/`\"E{}_1\x0d",
            "W0RMT-9>SYUYRP,WIDE1-1,WIDE2-1:`q&7p,bk/`\"Fv}_4\x0d",
            "W0RMT-9>SYUYQW,WIDE1-1,WIDE2-1:`q(cohbk/`\"G$}_4<\x0d",
            "W0RMT-9>SYUXSQ,WIDE1-1,WIDE2-1:`q*OlS\x1ek/`\"F`}145.310MHz email@gmail.com_4\x0d",
            "KB0TVJ-1>APJYC1,WIDE1-1:@215644h4003.25NI10512.42W&144.390MHz TOFF /A=5190 email@gmail.com\x0d",
            "KB0TVJ-1>APJYC1,WIDE1-1,WIDE2-1:@221244h4003.25NI10512.42W&144.390MHz TOFF /A=5190 email@gmail.com\x0d",
            "W0SKY-1>APDW17:;449.750  *111111z3947.30N/10518.19Wr449.750MHz Toff -500 DMR TS1 TG310847 SKYHUBLINK.COM",
            "W0JJG-9>3Y5SQZ,WIDE1-1,WIDE2-1:`q[0mTRk/`\"Ep}_%\x0d",
            "W7JPJ-9>SYSXSV,K5RHD-10,WIDE1*:`pH1l#%j/`\"G=}_%\x0d",
            "W0SKY-1>APDW17:;447.425  *111111z4027.08N/10645.12Wr447.425MHz -500 N2SKY YSF DIGITAL SKYHUBLINK.COM",
            "W0SKY-1>APDW17:;447.400  *111111z4118.63N/10527.18Wr447.400MHz -500 KE0DNL WIRES-X SKYHUBLINK.COM",
        )

        while True:
            # The other thread will notify us if it's time to shut down
            anything = self.pipe.poll(0.1)
            if anything:
                return
            
            if datetime.datetime.now() > next:
                next = datetime.datetime.now() + datetime.timedelta(seconds=random.randint(1, 4))
                message = random.choice(messages)
                global test_receiver_start_time
                diff = (datetime.datetime.now() - test_receiver_start_time)  # type: ignore
                altitude = int(diff.total_seconds() * 10 + 5280)
                message = re.sub(r"A=\d+", f"A={int(altitude):06}", message)
                longitude_d = 105 - diff.total_seconds() / 20000
                message = re.sub(r"10500.00", long_to_d_m_fm(longitude_d), message)
                self.pipe.send(message)


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


def long_to_d_m_fm(degrees: float) -> str:
    """Converts to DDDMM.MM format."""
    minutes = (degrees - int(degrees)) * 60
    return f"{int(degrees)}{minutes:05.2f}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="APRS Monitor",
        description="Monitors APRS packets for our balloon",
    )
    parser.add_argument(
        "--call-sign",
        action="store",
        type=str,
        dest="call_sign",
        default="KE0FZV",
        help="Your callsign",
    )
    parser.add_argument(
        "--launch-site",
        action="store",
        help="Set the launch site coordinates. Used in distance calculations. Example: '40.000,-105.000'. If not set, the first packet from the call sign will be assumed to be the position.",
        dest="launch_site",
    )
    parser.add_argument(
        "--interval",
        action="store",
        type=float,
        help="""The interval in seconds that our two trackers broadcast. The monitor will switch
between the frequencies to make sure to pick them both up, but will prefer to stay on APRS in order
to pick up other people.""",
        dest="interval_s",
        default=250,
    )
    parser.add_argument(
        "--aprs-only",
        action="store_true",
        default=False,
        help="Only monitor the APRS frequency, skip the RS41.",
        dest="aprs_only",
    )
    parser.add_argument(
        "--rs41-only",
        action="store_true",
        default=False,
        help="Only monitor the RS41 frequency, skip the APRS.",
        dest="rs41_only",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        default=False,
        help="Use fake messages instead of using the RTL-SDR, just for testing the display",
        dest="test",
    )
    parser_options = parser.parse_args()

    receiver_class = TestReceiver if parser_options.test else AprsReceiver

    if parser_options.launch_site:
        lat, long = [float(i) for i in parser_options.launch_site.split(",")]
        if lat < -90 or lat >= 90 or long < -180 or long > 180:
            raise ValueError("Bad launch site")
        launch_site = copy.deepcopy(DUMMY_APRS_MESSAGE)
        launch_site.latitude_d = lat
        launch_site.longitude_d = long
        setattr(get_launch_site, "launch_site", launch_site)

    options = Options(
        call_sign=parser_options.call_sign,
        interval_s=parser_options.interval_s,
        aprs_only=parser_options.aprs_only,
        rs41_only=parser_options.rs41_only,
        test=parser_options.test,
    )

    curses.wrapper(
        lambda stdscr: main(stdscr, receiver_class, options),
    )
