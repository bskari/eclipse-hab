"""Logs the internal temperature."""
import datetime
import logging
import os
import sys
import time


def main():
    """Main."""
    logger = logging.getLogger('temperature')
    formatter = logging.Formatter(
        '%(asctime)s:%(levelname)s %(message)s'
    )

    file_handler = logging.FileHandler('temperature.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    if len(sys.argv) > 2:
        swap_file_seconds = int(sys.argv[1])
    else:
        swap_file_seconds = 60 * 15

    if len(sys.argv) > 1:
        delay_seconds = int(sys.argv[0])
    else:
        delay_seconds = 10

    try:
        log_temperature(delay_seconds, swap_file_seconds)
    except Exception as exc:
        logger.error(exc)


def log_temperature(delay_seconds, swap_file_seconds):
    """Logs the internal temperature."""
    logger = logging.getLogger('temperature')

    logger.info(
        'delay_seconds: %d, swap_file_seconds: %d',
        delay_seconds,
        swap_file_seconds
    )

    temperature_path = 'temperatures'
    if not os.path.isdir(temperature_path):
        os.mkdir(temperature_path)

    if delay_seconds < 1:
        raise ValueError('Invalid delay_seconds ')

    if swap_file_seconds < 60:
        raise ValueError('Invalid swap_file_seconds')

    while True:
        seconds = 0
        temperature_file_name = temperature_path + os.sep + datetime.datetime.strftime(
            datetime.datetime.now(),
            '%Y-%m-%d_%H:%M:%S.csv'
        )
        logger.debug('Opening %s', temperature_file_name)
        with open(temperature_file_name, 'w') as temperature_file:
            while seconds < swap_file_seconds:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as thermal_zone_file:
                    temperature_c = float(thermal_zone_file.read()) * 1e-3
                logger.debug('%.2f C', temperature_c)

                time_stamp = datetime.datetime.strftime(
                    datetime.datetime.now(),
                    '%Y-%m-%d %H:%M:%S'
                )
                temperature_file.write('"{}",{}\n'.format(time_stamp, temperature_c))
                temperature_file.flush()
                time.sleep(delay_seconds)
                seconds += delay_seconds


if __name__ == '__main__':
    main()
