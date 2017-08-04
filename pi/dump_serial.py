import datetime
import os
import serial
import serial.tools.list_ports
import sys
import logging


def main():
    """Main."""
    logger = logging.getLogger('serial')
    stdout_handler = logging.StreamHandler(sys.stdout)
    # We'll be logging all of read messages to debug, and there might be a
    # bunch, so let's just dump the message and not include time stamps or
    # anything like that
    formatter = logging.Formatter('%(message)s')
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    ports = serial.tools.list_ports.comports()
    if len(ports) == 0:
        raise ValueError('No serial ports found')
    # TODO: Pick the correct port if there are more than one
    port_name, _, _ = ports[0]
    logger.info('Reading from %s', port_name)
    logger.setLevel(logging.DEBUG)
    dump_serial(port_name, logger)


def dump_serial(port_name, logger, seconds_between_timestamps=None):
    """Dumps the serial port to a file."""
    if seconds_between_timestamps is None:
        seconds_between_timestamps = 60

    serial_ = serial.Serial(port_name, timeout=seconds_between_timestamps)

    serial_path = 'serials'
    if not os.path.isdir(serial_path):
        os.mkdir(serial_path)

    serial_file_name = serial_path + os.sep + datetime.datetime.strftime(
        datetime.datetime.now(),
        '%Y-%m-%d_%H:%M:%S.log'
    )
    logger.debug('Opening %s', serial_file_name)

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
            if (now - last_timestamp).seconds > seconds_between_timestamps:
                time_stamp = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')

                serial_file.write('\n{}\n'.format(time_stamp).encode())
                serial_file.flush()

                logger.info('%s: read %d bytes', time_stamp, bytes_read_count)
                last_timestamp = now
                bytes_read_count = 0


if __name__ == '__main__':
    main()
