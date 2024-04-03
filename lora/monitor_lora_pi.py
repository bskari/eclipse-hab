"""Monitor data from the LoRa gateway Raspberry Pi."""

import argparse
import concurrent.futures
import curses
import dataclasses
import datetime
import json
import logging
import math
import socket
import sys
import threading
import time
import typing


# Balloon status
STATUS_LABELS_COUNT = 7
FT_PER_M = 3.2808399
MPH_PER_MPS = 2.2369363
MILES_PER_KM = 0.62137119
CALLSIGN = "KE0FZV"

logger = logging.getLogger(__file__)

@dataclasses.dataclass
class Windows:
    time: curses.window
    error: curses.window
    status: curses.window
    sentences: curses.window


@dataclasses.dataclass
class Options:
    ip: str
    port: int


@dataclasses.dataclass
class Status:
    index: int
    channel: int
    payload: str
    time: str  # e.g. "16:52:24"
    latitude_d: float
    longitude_d: float
    altitude_m: float
    snr: int
    rssi: int
    ferr: float
    temperature_c: float
    sentence: str  # e.g. "$$KE0FZV,328,16:52:24,39.99717,-105.22822,01543,0,0,0,18.9*8302"


@dataclasses.dataclass
class Position:
    latitude_d: float
    longitude_d: float
    altitude_m: float


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
    sentences_window = curses.newwin(lines, curses.COLS, STATUS_LABELS_COUNT + 5, 0)

    time_window.border()
    error_window.border()
    status_window.border()
    sentences_window.border()

    time_window.refresh()
    error_window.refresh()
    status_window.refresh()
    sentences_window.refresh()

    return Windows(
        time=time_window,
        error=error_window,
        status=status_window,
        sentences=sentences_window,
    )


def initialize_logger(windows: Windows) -> None:
    logger.setLevel(logging.DEBUG)
    handler = CursesHandler(windows.error)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    handler.setLevel(logging.WARN)
    logger.addHandler(handler)
    handler2 = logging.FileHandler("lora-debug.log")
    handler2.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s:%(lineno)s %(message)s"))
    handler2.setLevel(logging.DEBUG)
    logger.addHandler(handler2)


def update_time(window: curses.window) -> None:
    formatted = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
    _, max_x = window.getmaxyx()
    window.addnstr(1, 1, formatted, max_x - 2)
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


def update_status(window: curses.window, position: Status, time: datetime.datetime) -> None:
    if not hasattr(update_status, "recent_id"):
        setattr(update_status, "recent_id", None)

    # If there's not a new message, then we only need to update the seconds ago and estimates
    seconds_ago = (datetime.datetime.now() - time).total_seconds()
    _, max_x = window.getmaxyx()
    window.move(4, 1)
    window.clrtoeol()
    isecs = int(seconds_ago)
    ago = f"{isecs // 3600:02}:{(isecs // 60) % 60:02}:{isecs % 60:02}"
    window.addnstr(4, 1, f"Last seen: {ago} ago", max_x - 2)
    window.border()

    # If there's not a new message, then we only need to update the seconds ago and estimates
    if update_status.recent_id == id(position):  # type: ignore
        window.noutrefresh()
        return

    update_status.recent_id = id(position)  # type: ignore

    window.clear()
    window.border()
    window.addnstr(1, 1, f"Latitude: {position.latitude_d:.4f}", max_x - 2)
    window.addnstr(2, 1, f"Longitude: {position.longitude_d:.4f}", max_x - 2)
    window.addnstr(3, 1, f"Altitude: {position.altitude_m:.1f} m, {position.altitude_m * FT_PER_M:.1f} ft", max_x - 2)
    ago = f"{isecs // 3600:02}:{(isecs // 60) % 60:02}:{isecs % 60:02}"
    window.addnstr(4, 1, f"Last seen: {ago} ago", max_x - 2)
    window.addnstr(5, 1, f"Snr: {position.snr}", max_x - 2)
    window.addnstr(6, 1, f"Rssi: {position.rssi}", max_x - 2)
    # TODO Is this included in the message?
    window.addnstr(7, 1, f"Temperature: {position.temperature_c}°C, {position.temperature_c * 1.8 + 32:.0f}°F", max_x - 2)

    window.noutrefresh()


def update_sentences(window: curses.window, sentences: typing.List[typing.Tuple[datetime.datetime, str]]) -> None:
    """Show recently received APRS packets."""
    if not hasattr(update_sentences, "previous_sentence_count"):
        setattr(update_sentences, "previous_sentence_count", 0)
    if update_sentences.previous_sentence_count == len(sentences):  # type: ignore
        return

    window.clear()
    window.border()
    max_y, max_x = window.getmaxyx()
    # Show recent received sentences
    for sentence_index in range(0, max_y - 2):
        if sentence_index >= len(sentences):
            break
        time, sentence = sentences[-sentence_index - 1]
        timestamp = datetime.datetime.strftime(time, "%H:%M:%S")
        attributes = 0
        whole = f"{timestamp} {sentence}"
        window.addnstr(sentence_index + 1, 1, whole, max_x - 2, attributes)

    setattr(update_sentences, "previous_sentence_count", len(sentences))
    window.noutrefresh()


def update_screen(
    windows: Windows,
    recent_position: Status,
    recent_position_time: datetime.datetime,
    sentences: typing.List[typing.Tuple[datetime.datetime, str]],
) -> None:
    update_time(windows.time)
    update_error(windows.error)
    update_status(windows.status, recent_position, recent_position_time)
    update_sentences(windows.sentences, sentences)
    curses.doupdate()


def loop_forever(windows: Windows, options: Options) -> None:

    recent_status: Status = Status(
        index=0,
        channel=0,
        payload="",
        time="00:00:00",
        latitude_d=0.0,
        longitude_d=0.0,
        altitude_m=0.0,
        snr=0,
        rssi=0,
        ferr=0,
        temperature_c=0.0,
        sentence="<none>",
    )
    recent_status_time: datetime.datetime = datetime.datetime.now() - datetime.timedelta(hours=24)
    sentences: typing.List[typing.Tuple[datetime.datetime, str]] = []
    positions: typing.List[Position] = []


    class SocketListener(threading.Thread):
        def __init__(self, sock: socket.socket):
            self._sock = sock
            self.stop = False
            super().__init__()

        @staticmethod
        def parse_temperature(raw: str) -> float:
            try:
                return float(raw.split(",")[-1].split("*")[0])
            except:
                return 0.0
        
        def run(self):
            nonlocal recent_status
            nonlocal recent_status_time
            nonlocal sentences
            global CALLSIGN
            while not self.stop:
                try:
                    # There might be more than one, so split by newline
                    raw = self._sock.recv(4096)
                    if len(raw) == 4096:
                        # Ugh, we probably got too much data backed up and some got cut off. Just
                        # drop it.
                        continue

                    splits = raw.decode().split("\n")
                    for raw_sentence in splits:
                        stripped = raw_sentence.strip()
                        if len(stripped) == 0:
                            continue

                        logger.debug(stripped)
                        sentences.append((datetime.datetime.now(), stripped))

                        # Sample message:
                        # {
                        #   "class": "POSN",
                        #   "index": 0,
                        #   "channel": 0,
                        #   "payload": "KE0FZV",
                        #   "time": "16:52:24",
                        #   "lat": 39.99717,
                        #   "lon": -105.22822,
                        #   "alt": 1543,
                        #   "rate": 0.0,
                        #   "snr": 11,
                        #   "rssi": -68,
                        #   "ferr": -1.1,
                        #   "sentence": "$$KE0FZV,328,16:52:24,39.99717,-105.22822,01543,0,0,0,18.9*8302"
                        # }
                        parsed = json.loads(stripped.strip())
                        if parsed.get("class") == "POSN" and CALLSIGN in parsed.get("payload"):
                            sentence = parsed.get("sentence")
                            recent_status = Status(
                                index=parsed.get("index"),
                                channel=parsed.get("channel"),
                                payload=parsed.get("payload"),
                                time=parsed.get("time"),
                                latitude_d=parsed.get("lat"),
                                longitude_d=parsed.get("lon"),
                                altitude_m=parsed.get("alt"),
                                snr=parsed.get("snr"),
                                rssi=parsed.get("rssi"),
                                ferr=parsed.get("ferr"),
                                temperature_c=self.parse_temperature(sentence),
                                sentence=sentence,
                            )
                            recent_status_time = datetime.datetime.now()
                            positions.append(
                                Position(
                                    latitude_d=recent_status.latitude_d,
                                    longitude_d=recent_status.longitude_d,
                                    altitude_m=recent_status.altitude_m,
                                )
                            )

                except socket.timeout:
                    continue

                except Exception as exc:
                    logger.error(f"SocketListener exiting: {exc}", exc_info=exc)
                    break


    class GoogleEarthWriter(threading.Thread):
        def __init__(self):
            self.stop = False
            self._last_update = datetime.datetime.now() - datetime.timedelta(hours=4)
            super().__init__()
        
        def run(self):
            try:
                while not self.stop:
                    if (datetime.datetime.now() - self._last_update).seconds > 10:
                        self._last_update = datetime.datetime.now()
                        self._write_kml_file()
                
                    time.sleep(0.3)
            except Exception as exc:
                logger.error(f"GoogleEarthWriter exiting: {exc}", exc_info=exc)

        def _write_kml_file(self):
            nonlocal positions
            global CALLSIGN
            with open("lora.kml", "w") as file:
                file.write(f"""<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
        <Document>
            <name>Paths</name>
            <Placemark>
            <name>{CALLSIGN}</name>
            <description>{CALLSIGN} weather balloon LoRa</description>
            <Style>
                <LineStyle>
                <color>ff0000ff</color>
                <width>4</width>
                </LineStyle>
                <PolyStyle>
                <color>ff000000</color>
                </PolyStyle>
            </Style>
            <LineString>
                <extrude>1</extrude>
                <tessellate>1</tessellate>
                <altitudeMode>absolute</altitudeMode>
                <coordinates>\n""")
                if len(positions) > 0:
                    previous = positions[0]
                    for position in positions:
                        # We get so many messages, let's filter out ones where we don't move much
                        if distance_m(position, previous) > 10:
                            file.write(f"{position.longitude_d},{position.latitude_d},{position.altitude_m}\n")
                            previous = position
                file.write("""        </coordinates>
            </LineString>
            </Placemark>
        </Document>
        </kml>""")


    logger.debug("Starting")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((options.ip, options.port))
        sock.settimeout(0.5)
        listener = SocketListener(sock)
        listener.start()
        google_earth_writer = GoogleEarthWriter()
        google_earth_writer.start()
        while listener.is_alive:
            try:
                update_screen(windows, recent_status, recent_status_time, sentences)
                time.sleep(1)
            except KeyboardInterrupt:
                listener.stop = True
                google_earth_writer.stop = True
                logger.warning("Exiting...")
                update_error(windows.error)
                curses.doupdate()
                sock.close()
                time.sleep(1)
                sys.exit(1)


def find_lora_ip(port: int) -> typing.Optional[str]:
    """Find the Lora gateway's IP address"""
    def get_ip() -> typing.Optional[str]:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0)
            try:
                # Doesn't even have to be reachable
                sock.connect(("10.254.254.254", 1))
                ip = sock.getsockname()[0]
            except Exception:
                ip = None
        return ip

    def connect(address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            try:
                sock.connect((address, port))
                sock.close()
                return address
            except:
                return None
    
    def scan_range(partial_ip: str, low: int, high: int) -> typing.Optional[str]:
        low = max(0, low)
        high = min(255, high)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            print(f"Scanning for LoRa on {partial_ip}.{low}-{high}")
            addresses = (partial_ip + "." + str(octet) for octet in range(low, high))
            futures = [executor.submit(connect, address) for address in addresses]
            results = [f.result() for f in futures]
            for result in results:
                if result:
                    return result
        return None

    my_ip = get_ip()
    if my_ip is None:
        return None

    *parts, last_str = my_ip.split(".")
    partial = ".".join(parts)
    last_octet = int(last_str)

    # Try close IP addresses first
    result = scan_range(partial, last_octet - 10, last_octet + 10)
    if result:
        return result
    # Try them all
    step = 20
    for low in range(0, 256, step):
        result = scan_range(partial, low, low + step)
        if result:
            return result

    return None


def main(stdscr: curses.window, options: Options) -> None:
    windows = initialize_screen(stdscr)
    initialize_logger(windows)
    loop_forever(windows, options)


def distance_m(position1: Position, position2: Position) -> float:
    """Great circle distance."""
    lat1 = position1.latitude_d
    lat2 = position2.latitude_d
    long1 = position1.longitude_d
    long2 = position2.longitude_d
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
    parser = argparse.ArgumentParser(
        prog="LoRa gateway Raspberry Pi monitor",
        description="Monitors data from a LoRa gateway",
    )
    parser.add_argument(
        "--ip",
        action="store",
        type=str,
        dest="ip",
        default=None,
        help="The IP address of the LoRa gateway. e.g. 192.168.0.104. If not provided, will scan for it.",
    )
    parser.add_argument(
        "--port",
        action="store",
        type=int,
        dest="port",
        default=6004,
        help="The port the LoRa gateway is serving from.",
    )
    parser_options = parser.parse_args()

    if parser_options.ip is None:
        print("Scanning for LoRa gateway...")
        lora_ip = find_lora_ip(parser_options.port)
        print(f"Found LoRa gateway running on {lora_ip}")
        time.sleep(2)
    else:
        lora_ip = parser_options.ip
    if lora_ip is None:
        print("Unable to find LoRa gateway, is it running?")
        print("Or specify its IP address manually using --ip")
        sys.exit(1)

    options = Options(
        ip=lora_ip,
        port=parser_options.port,
    )
    curses.wrapper(
        lambda stdscr: main(stdscr, options)
    )
