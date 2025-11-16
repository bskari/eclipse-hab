import asyncio
import curses
import math
import sys
from datetime import datetime, UTC


def haversine(lat1, lon1, lat2, lon2, unit="km"):
    """
    Calculate the great-circle distance between two points 
    on the Earth given their latitude and longitude.

    lat1, lon1, lat2, lon2: coordinates in decimal degrees
    unit: "km" (default), "m", or "mi"
    """
    # Earth radius in different units
    R_km = 6371.0088
    R_mi = 3958.7613
    R_m  = R_km * 1000

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    if unit == "km":
        return R_km * c
    elif unit == "m":
        return R_m * c
    elif unit == "mi":
        return R_mi * c
    else:
        raise ValueError("unit must be 'km', 'm', or 'mi'")
 

async def read_stdin(queue):
    """Read stdin asynchronously and push complete lines to an asyncio queue."""
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:  # EOF
            await asyncio.sleep(0.1)
            continue
        await queue.put(line.decode().rstrip("\n"))


async def ui(stdscr, queue):
    """Main curses UI loop."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.clear()

    header = "timestamp,serial,frame,lat,lon,alt,vel_v,vel_h,heading,temp,humidity,pressure,type,freq_mhz,snr,f_error_hz,sats,batt_v,burst_timer,aux_data"
    fields = header.split(",")
    data = []
    previous_timestamp = None
    previous_position = None
    my_position = None

    try:
        with open("../station.cfg") as file:
            my_latitude = None
            my_longitude = None
            for line in file:
                if line.startswith("station_lat = "):
                    my_latitude = float(line.replace("station_lat = ", "").strip())
                if line.startswith("station_lon = "):
                    my_longitude = float(line.replace("station_lon = ", "").strip())
        if my_latitude is not None and my_longitude is not None:
            my_position = (my_latitude, my_longitude)

    except Exception as exc:
        print(f"Couldn't read station position: {exc}")
    if my_position is not None:
        print("Couldn't read station position")

    start = datetime.now()

    while True:
        # --- Process input lines if any ---
        try:
            while True:  # drain queue
                line = queue.get_nowait()
                data = [p.strip() for p in line.split(",")]

                # Remove trailing 'Z' because fromisoformat doesn't accept it directly
                previous_timestamp = datetime.fromisoformat(data[0].replace("Z", "+00:00"))

                previous_position = (float(data[3]), float(data[4]))


        except asyncio.QueueEmpty:
            pass

        # --- Update time ---
        now = datetime.now().strftime("%H:%M:%S")
        stdscr.addstr(0, 0, f"Time: {now}")
        if previous_timestamp is not None:
            utc_now = datetime.now(UTC)
            utc_now = utc_now.replace(tzinfo=None)
            previous_timestamp = previous_timestamp.replace(tzinfo=None)
            seconds_ago = (utc_now - previous_timestamp).total_seconds()
            stdscr.addstr(1, 0, f"Seconds ago: {int(seconds_ago)}      ")
        else:
            stdscr.addstr(1, 0, f"Seconds ago: unknown      ")

        # --- Update distance ---
        if previous_position is not None and my_position is not None:
            distance_km = haversine(previous_position[0], previous_position[1], my_position[0], my_position[1], "km")
            stdscr.addstr(2, 0, f"Distance: {round(distance_km, 2)} km     ")
        else:
            stdscr.addstr(2, 0, f"Distance: unknown     ")

        # --- Display fields ---
        for i, val in enumerate(fields):
            if i < len(data):
                datum = data[i]
            else:
                datum = ""
            stdscr.addstr(i + 3, 0, f"{fields[i]}: {datum}     ")

        stdscr.refresh()

        # Reload the display with data right away
        if (datetime.now() - start).total_seconds() > .1:
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(0.01)


async def main_curses(stdscr):
    queue = asyncio.Queue()
    await asyncio.gather(
        read_stdin(queue),
        ui(stdscr, queue)
    )


def main():
    curses.wrapper(lambda stdscr: asyncio.run(main_curses(stdscr)))


if __name__ == "__main__":
    main()
