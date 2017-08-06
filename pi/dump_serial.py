import datetime
import os
import serial
import serial.tools.list_ports
import sys
import logging

import sup800f


SUP800F_BAUDRATE = 115200
TRACKSOAR_BAUDRATE = 9600


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
    logger.setLevel(logging.DEBUG)
    logger.info('Found %d ports, reading from %s', len(ports), port_name)

    serial_ = serial.Serial(port_name, baudrate=SUP800F_BAUDRATE, timeout=60)
    if check_for_sup800f(serial_, logger):
        logger.info('Setting baudrate to %d', SUP800F_BAUDRATE)
        logger.info('Connected to SUP800F, switching it to binary mode')
        sup800f.switch_to_binary_mode(serial_)
        dump_sup800f_binary_messages(serial_, logger)
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


def dump_sup800f_binary_messages(serial_, logger):
    """Dumps the SUP800F binary messages from serial to a file."""
    serial_path = 'serials'
    if not os.path.isdir(serial_path):
        os.mkdir(serial_path)

    serial_file_name = serial_path + os.sep + datetime.datetime.strftime(
        datetime.datetime.now(),
        '%Y-%m-%d_%H:%M:%S.log'
    )
    logger.debug('Opening %s', serial_file_name)

    last_timestamp = datetime.datetime.now()
    message_count = 0

    with open(serial_file_name, 'wb') as serial_file:
        message_count = 0

        while True:
            message_bytes = sup800f.get_message(serial_)
            # The SUP800F dumps some other type of message that's 66 bytes long.
            # We only care about the binary stuff, which is always 41.
            if len(message_bytes) != 41:
                continue
            message_count += 1
            # We'll process and format these binary messages offline later
            serial_file.write(message_bytes)

            now = datetime.datetime.now()
            if (now - last_timestamp).seconds > serial_.timeout:
                time_stamp = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')

                serial_file.write('\n{}\n'.format(time_stamp).encode())
                serial_file.flush()

                logger.info('%s: read %d messages', time_stamp, message_count)
                if message_bytes is not None:
                    message = sup800f.parse_binary(message_bytes)
                    if message is not None:
                        logger.debug(
                                'G %.3f %.3f %.3f M %.3f %.3f %.3f P %d C %.3f',
                                message.acceleration_g_x,
                                message.acceleration_g_y,
                                message.acceleration_g_z,
                                message.magnetic_flux_ut_x,
                                message.magnetic_flux_ut_y,
                                message.magnetic_flux_ut_z,
                                message.pressure_p,
                                message.temperature_c,
                        )
                    last_timestamp = now
                message_count = 0



def check_for_sup800f(serial_, logger):
    """Cheks for SUP800F connected to the serial port."""
    logger.debug('Checking for SUP800F')
    try:
        sup800f.get_message(serial_, timeout_bytes=200)
    except ValueError:
        logger.debug('No SUP800F found')
        return False

    logger.debug('Found SUP800F')
    return True


if __name__ == '__main__':
    main()
