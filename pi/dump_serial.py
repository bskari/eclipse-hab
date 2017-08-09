import datetime
import os
import serial
import serial.tools.list_ports
import sys
import logging

import sup800f


SUP800F_BAUDRATE = 115200
TRACKSOAR_BAUDRATE = 9600


def main(verbose):
    """Main."""
    logger = logging.getLogger('serial')
    stdout_handler = logging.StreamHandler(sys.stdout)
    # We'll be logging all of read messages to debug, and there might be a
    # bunch, so let's just dump the message and not include time stamps or
    # anything like that
    formatter = logging.Formatter('%(message)s')
    stdout_handler.setFormatter(formatter)
    if verbose:
        stdout_handler.setLevel(logging.DEBUG)
    else:
        stdout_handler.setLevel(logging.INFO)
    logger.addHandler(stdout_handler)

    ports = serial.tools.list_ports.comports()
    if len(ports) == 0:
        raise ValueError('No serial ports found')
    # TODO: Pick the correct port if there are more than one
    port_name, _, _ = ports[0]
    logger.setLevel(logging.DEBUG)
    logger.info('Found %d ports, reading from %s', len(ports), port_name)

    serial_ = serial.Serial(port_name, baudrate=SUP800F_BAUDRATE, timeout=60)
    if check_for_sup800f(serial_, logger):
        logger.info('Setting baudrate to %d', SUP800F_BAUDRATE)
        logger.info('Connected to SUP800F, switching it to binary mode')
        sup800f.switch_to_binary_mode(serial_)
        dump_serial(serial_, logger)
    else:
        # Well, must be TrackSoar then
        logger.info('Setting baudrate to %d', TRACKSOAR_BAUDRATE)
        serial_.baudrate = TRACKSOAR_BAUDRATE
        dump_serial(serial_, logger)


def dump_serial(serial_, logger):
    """Dumps the serial port to a file."""
    serial_path = 'serials'
    if not os.path.isdir(serial_path):
        os.mkdir(serial_path)

    serial_file_name = serial_path + os.sep + datetime.datetime.strftime(
        datetime.datetime.now(),
        '%Y-%m-%d_%H:%M:%S.log'
    )
    logger.info('Opening %s', serial_file_name)

    last_timestamp = datetime.datetime.now()

    with open(serial_file_name, 'wb') as serial_file:
        bytes_read_count = 0

        while True:
            data = serial_.read(256)
            bytes_read_count += len(data)
            if len(data) > 0:
                logger.debug(data)
            serial_file.write(data)

            now = datetime.datetime.now()
            if (now - last_timestamp).seconds > serial_.timeout:
                # Grab the rest of the bytes so that we don't cut anything off
                previous_timeout = serial_.timeout
                # At 9600 baud, we should see... 1200 chars per second? so 0.01
                # seconds should be enough to wait if there are data coming
                # through
                serial_.timeout = 0.01
                data = b'1'
                while len(data) > 0:
                    data = serial_.read(256)
                    bytes_read_count += len(data)
                    if len(data) > 0:
                        logger.debug(data)
                    serial_file.write(data)
                serial_.timeout = previous_timeout

                time_stamp = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')

                serial_file.write('\n{}\n'.format(time_stamp).encode())
                serial_file.flush()

                logger.info('%s: read %d bytes', time_stamp, bytes_read_count)
                last_timestamp = now
                bytes_read_count = 0


def check_for_sup800f(serial_, logger):
    """Cheks for SUP800F connected to the serial port."""
    logger.info('Checking for SUP800F')
    # First, check if we're seeing PSTI messages. SUP800F loves dumping those
    # in NMEA mode, and I don't think you can turn them off.
    old_timeout_s = serial_.timeout

    # These should be spewing out at least once per second, so 5 should be safe
    serial_.timeout = 5

    def inner(serial_):
        """Helper function to check for SUP800F. Defined as a convenience so
        that I don't have a bunch of function return points where I need to
        remember to reset the timeout.
        """
        try:
            line = serial_.readline()
            if line.startswith(b'$PSTI'):
                return True
        except TimeoutError:
            return False

        try:
            sup800f.get_message(serial_, timeout_bytes=200)
        except ValueError:
            logger.info('No SUP800F found')
            return False

        logger.info('Found SUP800F')
        return True

    found = inner(serial_)
    serial_.timeout = old_timeout_s
    return found


if __name__ == '__main__':
    verbose = ('-v' in sys.argv or '--verbose' in sys.argv)
    main(verbose)
